"""Pruebas del ejercicio m17-e7."""

import json
import shutil
import sqlite3
import time
from pathlib import Path

import pytest

import carga_masiva as cm

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]


def contar(ruta_bd, sql):
    with sqlite3.connect(ruta_bd) as con:
        return con.execute(sql).fetchone()[0]


@pytest.fixture
def bd(tmp_path):
    return tmp_path / "telco.db"


def test_resultado(bd):
    r = cm.cargar_cdr(DATOS, bd)
    assert r["leidos"] == ESPERADO["registros_totales"]
    assert r["validos"] == ESPERADO["registros_validos"]
    assert r["rechazados"] == ESPERADO["registros_totales"] - ESPERADO["registros_validos"]
    assert r["errores"] == ESPERADO["errores"]
    assert list(r["errores"]) == cm.ERRORES


def test_tablas(bd):
    cm.cargar_cdr(DATOS, bd)
    assert contar(bd, "SELECT COUNT(*) FROM cdr") == ESPERADO["registros_validos"]
    assert contar(bd, "SELECT COUNT(*) FROM rechazos") == ESPERADO["registros_totales"] - ESPERADO["registros_validos"]
    assert contar(bd, "SELECT COUNT(*) FROM rechazos WHERE motivo = 'duplicado'") == ESPERADO["errores"]["duplicado"]
    assert contar(bd, "SELECT COUNT(*) FROM paso_cdr") == 0, "Vacía la tabla de paso al terminar"
    assert contar(bd, "SELECT typeof(duracion_seg) FROM cdr LIMIT 1") == "integer"
    assert contar(bd, "SELECT typeof(mb) FROM cdr LIMIT 1") == "real"
    minutos = contar(bd, "SELECT SUM((duracion_seg + 59) / 60) FROM cdr WHERE tipo = 'VOZ' AND destino <> 'INTERNACIONAL'")
    assert minutos == ESPERADO["minutos_nacionales"]


def test_indices(bd):
    cm.cargar_cdr(DATOS, bd)
    with sqlite3.connect(bd) as con:
        indices = {f[0] for f in con.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
    assert {"ix_cdr_linea", "ix_cdr_fecha"} <= indices


def test_repetible(bd):
    cm.cargar_cdr(DATOS, bd)
    segunda = cm.cargar_cdr(DATOS, bd)
    assert segunda["leidos"] == ESPERADO["registros_totales"]
    assert contar(bd, "SELECT COUNT(*) FROM cdr") == ESPERADO["registros_validos"], "Repetir la carga no duplica"
    assert contar(bd, "SELECT COUNT(*) FROM rechazos") == ESPERADO["registros_totales"] - ESPERADO["registros_validos"]


@pytest.mark.parametrize("lote", [250, 1000, 100_000])
def test_cualquier_lote(tmp_path, lote):
    r = cm.cargar_cdr(DATOS, tmp_path / f"bd_{lote}.db", lote=lote)
    assert r["validos"] == ESPERADO["registros_validos"] and r["errores"] == ESPERADO["errores"]


def test_rapido(tmp_path):
    """150 000 filas en pocos segundos: imposible con un commit por fila."""
    carpeta = tmp_path / "grande"
    carpeta.mkdir()
    shutil.copy(DATOS / "clientes.csv", carpeta)
    cabecera, *filas = (DATOS / "cdr.csv").read_text(encoding="utf-8").splitlines()
    with open(carpeta / "cdr.csv", "w", encoding="utf-8", newline="\n") as f:
        f.write(cabecera + "\n")
        n = 0
        while n < 150_000:
            for fila in filas:
                n += 1
                f.write(f"{n}|{fila.split('|', 1)[1]}\n")
    inicio = time.perf_counter()
    r = cm.cargar_cdr(carpeta, tmp_path / "grande.db", lote=20_000)
    segundos = time.perf_counter() - inicio
    assert r["leidos"] == n
    assert segundos < 30, f"Tardó {segundos:.1f} s"


def test_usa_executemany():
    texto = (Path(__file__).parent / "carga_masiva.py").read_text(encoding="utf-8")
    assert "executemany" in texto
