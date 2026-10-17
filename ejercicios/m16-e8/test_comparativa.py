"""Pruebas del ejercicio m16-e8."""

import json
import time
from pathlib import Path

import pytest

import comparativa as c

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
CODIGO = (Path(__file__).parent / "comparativa.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("nombre", ["con_python", "con_pandas", "con_polars", "con_duckdb"])
def test_cada_herramienta_da_lo_esperado(nombre):
    r = getattr(c, nombre)(DATOS)
    assert sorted(r) == sorted(c.CLAVES)
    for clave in c.CLAVES:
        if clave == "mb_totales":
            assert abs(r[clave] - ESPERADO[clave]) < 0.01, f"{nombre}: mb_totales"
        else:
            assert r[clave] == ESPERADO[clave], f"{nombre}: {clave} = {r[clave]}, se esperaba {ESPERADO[clave]}"
        assert type(r[clave]) in (int, float), f"{nombre}: {clave} debe ser int o float de Python, no {type(r[clave])}"


def test_cada_funcion_usa_su_herramienta():
    bloques = CODIGO.split("\ndef ")
    cuerpo = {b.split("(", 1)[0]: b for b in bloques}
    assert "csv" in cuerpo["con_python"] and "pd." not in cuerpo["con_python"]
    assert "pd." in cuerpo["con_pandas"]
    assert "scan_csv" in cuerpo["con_polars"]
    assert "duckdb" in cuerpo["con_duckdb"]


def test_medir():
    llamadas = []

    def lenta(x):
        llamadas.append(x)
        datos = b"x" * (60 * 1024 * 1024)  # 60 MB escritos de verdad
        time.sleep(0.3)
        return len(datos) + x

    m = c.medir(lenta, 1)
    assert llamadas == [1], "La función se ejecuta exactamente una vez"
    assert m["resultado"] == 60 * 1024 * 1024 + 1
    assert 0.25 < m["segundos"] < 3
    assert 50 < m["memoria_mb"] < 500, "memoria_mb es lo que creció el proceso: debe incluir los 60 MB de la función"
