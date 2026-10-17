"""Pruebas de contrato del Proyecto 2. Ejecuta: python -m pytest proyectos/p2-conciliacion -v"""

import ast
from pathlib import Path

import pandas as pd
import pytest

from conciliacion import conciliacion, facturacion, lectura, reporte, validacion

SRC = Path(__file__).resolve().parents[1] / "src" / "conciliacion"


# --- lectura -----------------------------------------------------------------------------

def test_lectura_tipos(datos):
    assert pd.api.types.is_string_dtype(datos.cdr["linea_origen"])
    assert pd.api.types.is_string_dtype(datos.clientes["linea"])
    assert (datos.cdr["linea_origen"] == "").any(), "Los vacíos del CDR deben quedar como texto vacío"
    assert len(datos.facturas) == len(datos.clientes)


def test_lectura_archivo_faltante(tmp_path):
    with pytest.raises(FileNotFoundError):
        lectura.leer_datos(tmp_path)


# --- validación ------------------------------------------------------------------------------

def test_clasificacion(datos, esperado):
    clasif = validacion.clasificar(datos.cdr, datos.clientes)
    assert len(clasif) == len(datos.cdr)
    conteo = clasif.value_counts()
    for error, cantidad in esperado["cdr"]["errores"].items():
        assert int(conteo.get(error, 0)) == cantidad, error
    assert int(conteo.get("valido", 0)) == esperado["cdr"]["registros_validos"]


# --- facturación -------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def correctas(datos):
    clasif = validacion.clasificar(datos.cdr, datos.clientes)
    consumo = facturacion.consumo_por_linea(datos.cdr[clasif == "valido"])
    return consumo, facturacion.facturas_correctas(datos.clientes, datos.planes, consumo)


def test_consumo(correctas, esperado):
    consumo, _ = correctas
    assert int(consumo["minutos_nacionales"].sum()) == esperado["cdr"]["minutos_nacionales"]
    assert int(consumo["minutos_internacionales"].sum()) == esperado["cdr"]["minutos_internacionales"]
    assert abs(float(consumo["mb"].sum()) - esperado["cdr"]["mb_totales"]) < 0.01
    assert int(consumo["sms"].sum()) == esperado["cdr"]["sms_totales"]


def test_facturas_correctas(correctas, datos, esperado):
    _, fc = correctas
    columnas = ["cliente_id", "cargo_fijo", "valor_voz", "valor_internacional", "valor_datos", "valor_sms",
                "descuento", "subtotal", "iva", "total"]
    assert list(fc.columns) == columnas
    assert len(fc) == len(datos.clientes)
    assert int(fc["total"].sum()) == esperado["facturacion"]["total_correcto"]
    assert int(fc["iva"].sum()) == esperado["facturacion"]["iva_correcto"]
    assert (fc["total"] == fc["subtotal"] + fc["iva"]).all()


def test_regla_de_iva_comercial():
    clientes = pd.DataFrame({"cliente_id": ["C1"], "linea": ["3001"], "plan_id": ["P"], "segmento": ["RESIDENCIAL"],
                             "fecha_alta": ["2015-01-01"]})
    planes = pd.DataFrame({"plan_id": ["P"], "segmento": ["RESIDENCIAL"], "cargo_fijo": [38150], "minutos_incluidos": [0],
                           "mb_incluidos": [0], "sms_incluidos": [0], "tarifa_minuto": [0], "tarifa_minuto_internacional": [0],
                           "tarifa_mb": [0], "tarifa_sms": [0]})
    consumo = pd.DataFrame(columns=["minutos_nacionales", "minutos_internacionales", "mb", "sms"])
    fc = facturacion.facturas_correctas(clientes, planes, consumo)
    assert int(fc["iva"].iloc[0]) == 7249, "El IVA de 38.150 es 7.248,5 → 7.249 (0,5 sube)"


# --- conciliación ------------------------------------------------------------------------------------------

def test_conciliacion(correctas, datos, esperado):
    _, fc = correctas
    diag = conciliacion.conciliar(fc, datos.facturas)
    assert list(diag.columns) == ["cliente_id", "factura_id", "motivo", "total_correcto", "total_facturado", "diferencia"]
    resumen = conciliacion.resumen(diag, fc, datos.facturas)
    for clave, valor in esperado["facturacion"].items():
        if clave in resumen:
            assert resumen[clave] == valor, clave
    for clave in ["facturas", "total_facturado", "total_correcto", "facturas_total_distinto", "diferencia_total",
                  "facturas_inconsistentes", "facturas_con_diferencia_consumo"]:
        assert clave in resumen, f"Falta la clave {clave} en el resumen"
    assert sum(m["facturas"] for m in resumen["por_motivo"].values()) == len(diag)


# --- reporte y CLI --------------------------------------------------------------------------------------------

def test_reporte(correctas, datos, tmp_path):
    _, fc = correctas
    diag = conciliacion.conciliar(fc, datos.facturas)
    ruta = reporte.generar(conciliacion.resumen(diag, fc, datos.facturas), diag, tmp_path)
    assert ruta == tmp_path / "reporte.md"
    texto = ruta.read_text(encoding="utf-8")
    assert "](diferencias_por_motivo.png)" in texto and "](top_diferencias.png)" in texto
    for png in ["diferencias_por_motivo.png", "top_diferencias.png"]:
        assert (tmp_path / png).read_bytes()[:4] == b"\x89PNG"
    assert (tmp_path / "diferencias.csv").read_bytes()[:3] == b"\xef\xbb\xbf"


def test_cli_cuadra(carpeta_datos, tmp_path):
    from conciliacion.cli import main

    assert main(["--datos", str(carpeta_datos), "--salida", str(tmp_path)]) == 0
    assert (tmp_path / "reporte.md").exists()
    assert (tmp_path / "conciliacion.log").exists()


def test_cli_sin_datos(tmp_path):
    from conciliacion.cli import main

    assert main(["--datos", str(tmp_path / "no_existe"), "--salida", str(tmp_path / "salida")]) == 2


# --- arquitectura ----------------------------------------------------------------------------------------------

def imports_de(modulo):
    arbol = ast.parse((SRC / f"{modulo}.py").read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
        elif isinstance(nodo, ast.Import):
            nombres |= {a.name for a in nodo.names}
    return nombres


@pytest.mark.parametrize("modulo", ["validacion", "facturacion", "conciliacion"])
def test_logica_no_toca_archivos(modulo):
    texto = (SRC / f"{modulo}.py").read_text(encoding="utf-8")
    assert "read_csv" not in texto and "open(" not in texto and "to_csv" not in texto, (
        f"{modulo}.py es lógica de negocio: no debe leer ni escribir archivos"
    )
    assert "conciliacion.cli" not in imports_de(modulo) and "conciliacion.reporte" not in imports_de(modulo)
