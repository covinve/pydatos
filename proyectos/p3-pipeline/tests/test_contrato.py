"""Pruebas de contrato del Proyecto 3. Ejecuta: python -m pytest proyectos/p3-pipeline -v"""

import json
import shutil

import duckdb
import pandas as pd
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from telco_pipeline import anomalias, conciliacion, config, consumo, facturacion, lectura, pipeline, reporte
from telco_pipeline.cli import app

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]


# --- configuración -------------------------------------------------------------------------

def test_config_por_defecto_y_capas(tmp_path, monkeypatch):
    c = config.crear_config()
    assert (c.periodo, c.memoria_duckdb, c.hilos, c.umbral_rechazo, c.top_anomalias) == ("202609", "4GB", 4, 5.0, 20)
    toml = tmp_path / "config.toml"
    toml.write_text('periodo = "202608"\nhilos = 8\nmemoria_duckdb = "8gb"\n', encoding="utf-8")
    env = tmp_path / "local.env"
    env.write_text("TELCO_HILOS=12\n", encoding="utf-8")
    c = config.crear_config(toml, env)
    assert (c.periodo, c.hilos, c.memoria_duckdb) == ("202608", 12, "8GB")
    monkeypatch.setenv("TELCO_HILOS", "16")
    assert config.crear_config(toml, env, periodo="202610", hilos=None).hilos == 16
    assert config.crear_config(toml, env, periodo="202610").periodo == "202610"


@pytest.mark.parametrize("campo, valor", [("periodo", "202613"), ("memoria_duckdb", "8TB"), ("hilos", 0),
                                          ("umbral_rechazo", 101), ("top_anomalias", 0)])
def test_config_invalida(campo, valor):
    with pytest.raises(ValidationError):
        config.crear_config(**{campo: valor})


# --- lectura y validación ---------------------------------------------------------------------

def test_lectura(carpeta_datos, tmp_path):
    t = lectura.leer_tablas(carpeta_datos)
    assert pd.api.types.is_string_dtype(t.clientes["linea"]) and pd.api.types.is_string_dtype(t.facturas["linea"])
    assert len(t.facturas) == len(t.clientes)
    with pytest.raises(FileNotFoundError, match="cdr.csv"):
        lectura.leer_tablas(tmp_path)


def test_validacion_resumen(validado, esperado):
    r, _ = validado
    e = esperado["cdr"]
    for clave in ("registros_totales", "registros_validos", "minutos_nacionales", "minutos_internacionales", "sms_totales"):
        assert r[clave] == e[clave], clave
    assert r["errores"] == e["errores"] and list(r["errores"]) == ERRORES
    assert abs(r["mb_totales"] - e["mb_totales"]) < 0.01


def test_validacion_parquet(validado, esperado):
    _, salida = validado
    validos = (salida / "validos.parquet").as_posix()
    n, distintos = duckdb.sql(f"SELECT COUNT(*), COUNT(DISTINCT cdr_id) FROM '{validos}'").fetchone()
    assert n == distintos == esperado["cdr"]["registros_validos"]
    tipos = dict(duckdb.sql(f"DESCRIBE SELECT * FROM '{validos}'").fetchall()[i][:2] for i in range(9))
    assert tipos["fecha_inicio"].startswith("TIMESTAMP") and tipos["duracion_seg"] == "INTEGER"
    assert tipos["mb"] == "DOUBLE" and tipos["cdr_id"] == "BIGINT"
    rechazos = (salida / "rechazos.parquet").as_posix()
    por_motivo = dict(duckdb.sql(f"SELECT motivo, COUNT(*) FROM '{rechazos}' GROUP BY motivo").fetchall())
    assert por_motivo == {k: v for k, v in esperado["cdr"]["errores"].items() if v}


# --- consumo y facturación ----------------------------------------------------------------------

def test_consumo(validado, esperado):
    _, salida = validado
    c = consumo.consumo_por_linea(salida / "validos.parquet")
    assert list(c.columns) == ["minutos_nacionales", "minutos_internacionales", "mb", "sms"]
    assert c.index.name == "linea" and len(c) == esperado["cdr"]["lineas_con_consumo"]
    assert int(c["minutos_nacionales"].sum()) == esperado["cdr"]["minutos_nacionales"]
    assert abs(float(c["mb"].sum()) - esperado["cdr"]["mb_totales"]) < 0.01


def test_perfil(validado):
    _, salida = validado
    p = consumo.perfil_lineas(salida / "validos.parquet")
    assert list(p.columns) == ["llamadas", "minutos", "pct_internacional", "pct_nocturno", "mb", "sms"]
    assert p["pct_internacional"].between(0, 1).all() and p["pct_nocturno"].between(0, 1).all()


@pytest.fixture(scope="module")
def correctas(validado, carpeta_datos):
    _, salida = validado
    t = lectura.leer_tablas(carpeta_datos)
    return t, facturacion.facturas_correctas(t.clientes, t.planes, consumo.consumo_por_linea(salida / "validos.parquet"))


def test_facturas_correctas(correctas, esperado):
    t, fc = correctas
    assert list(fc.columns) == ["linea", "cliente_id", "plan_id", "segmento", "cargo_fijo", "valor_voz",
                                "valor_internacional", "valor_datos", "valor_sms", "descuento", "subtotal", "iva", "total"]
    assert len(fc) == len(t.clientes)
    assert int(fc["total"].sum()) == esperado["facturacion"]["total_correcto"]
    assert int(fc["iva"].sum()) == esperado["facturacion"]["iva_correcto"]
    assert (fc["total"] == fc["subtotal"] + fc["iva"]).all()


def test_reglas_puntuales():
    assert list(facturacion.redondear([0.5, 1.49, 2.5, 7778.6])) == [1, 1, 3, 7779]
    assert list(facturacion.excedente([342, 100, 5000], [300, 300, -1], [120, 120, 0])) == [5040, 0, 0]


def test_conciliacion(correctas, esperado):
    t, fc = correctas
    diferencias, resumen = conciliacion.conciliar(t.facturas, fc)
    assert resumen == esperado["facturacion"]
    assert list(diferencias.columns) == ["factura_id", "linea", "plan_id", "motivo", "facturado", "correcto", "diferencia"]
    assert len(diferencias) == esperado["facturacion"]["facturas_total_distinto"]
    assert set(diferencias["motivo"]) <= {"consumo", "inconsistente", "otro"}
    assert list(diferencias["diferencia"].abs()) == sorted(diferencias["diferencia"].abs(), reverse=True)


# --- anomalías ------------------------------------------------------------------------------------

def test_anomalias(validado):
    _, salida = validado
    p = consumo.perfil_lineas(salida / "validos.parquet")
    a, b = anomalias.puntuar(p), anomalias.puntuar(p)
    assert (a == b).all() and list(a.index) == list(p.index)
    t = anomalias.top(p, 5)
    assert len(t) == 5 and list(t["puntaje"]) == sorted(t["puntaje"], reverse=True)


# --- pipeline, reporte y CLI ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def ejecucion(tmp_path_factory, carpeta_datos):
    salidas = tmp_path_factory.mktemp("salidas")
    c = config.crear_config(datos=carpeta_datos, salidas=salidas, memoria_duckdb="500MB", hilos=2)
    return pipeline.ejecutar(c), salidas / "202609"


def test_pipeline(ejecucion, esperado):
    r, _ = ejecucion
    assert r["cuadra"] is True and r["alerta_rechazo"] is False
    assert r["facturacion"] == esperado["facturacion"]
    assert set(r["tiempos"]) == {"validacion", "facturacion", "conciliacion", "anomalias", "reporte"}
    assert r["anomalias"] == 20


def test_reporte(ejecucion):
    r, salida = ejecucion
    for nombre in ("resumen.json", "diferencias.csv", "anomalias.csv", "rechazos.png", "informe.md",
                   "validos.parquet", "rechazos.parquet"):
        assert (salida / nombre).exists(), nombre
    resumen = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["facturacion"] == r["facturacion"]
    assert (salida / "diferencias.csv").read_bytes().startswith(b"\xef\xbb\xbf"), "CSV con BOM para Excel"
    texto = (salida / "informe.md").read_text(encoding="utf-8")
    for seccion in ("# Pipeline de facturación · periodo 202609", "## Resumen", "## Mayores diferencias",
                    "## Líneas sospechosas", "## Tiempos", "![Rechazos por motivo](rechazos.png)"):
        assert seccion in texto, seccion
    assert reporte.pesos(r["facturacion"]["total_facturado"]) in texto


def test_cli(tmp_path, carpeta_datos):
    runner = CliRunner()
    r = runner.invoke(app, ["ejecutar", "--datos", str(carpeta_datos), "--salidas", str(tmp_path)])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "202609" / "pipeline.log").exists()
    assert runner.invoke(app, ["ejecutar", "--periodo", "202699"]).exit_code == 2
    assert runner.invoke(app, ["ejecutar", "--datos", str(tmp_path / "no_existe")]).exit_code == 2


def test_cli_no_cuadra(tmp_path, carpeta_datos):
    copia = tmp_path / "datos"
    shutil.copytree(carpeta_datos, copia)
    e = json.loads((copia / "esperado.json").read_text(encoding="utf-8"))
    e["facturacion"]["total_correcto"] += 1
    (copia / "esperado.json").write_text(json.dumps(e), encoding="utf-8")
    r = CliRunner().invoke(app, ["ejecutar", "--datos", str(copia), "--salidas", str(tmp_path / "s")])
    assert r.exit_code == 1
