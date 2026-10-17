"""Pruebas del ejercicio m16-e7."""

import json
from pathlib import Path

import duckdb
import pytest

import validar_duckdb as v

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    salida = tmp_path_factory.mktemp("duckdb")
    return v.procesar(DATOS, salida, memoria="500MB"), salida


@pytest.mark.parametrize("clave", ["registros_totales", "registros_validos", "errores", "minutos_nacionales",
                                   "minutos_internacionales", "mb_totales", "sms_totales"])
def test_resumen(resultado, clave):
    r, _ = resultado
    if clave == "mb_totales":
        assert abs(r[clave] - ESPERADO[clave]) < 0.01
    else:
        assert r[clave] == ESPERADO[clave]


def test_parquet_de_validos(resultado):
    _, salida = resultado
    filas = duckdb.sql(f"SELECT COUNT(*), COUNT(DISTINCT cdr_id) FROM '{salida / 'validos.parquet'}'").fetchone()
    assert filas == (ESPERADO["registros_validos"], ESPERADO["registros_validos"])


def test_rechazos(resultado):
    _, salida = resultado
    total = duckdb.sql(f"SELECT COUNT(*) FROM read_csv('{salida / 'rechazos.csv'}', header=true)").fetchone()[0]
    assert total == sum(ESPERADO["errores"].values())
