"""Pruebas del ejercicio m14-e7."""

import json
from pathlib import Path

import pytest

import por_bloques as p

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
CLAVES = ["registros_totales", "registros_validos", "errores", "minutos_nacionales",
          "minutos_internacionales", "mb_totales", "sms_totales"]


@pytest.mark.parametrize("tamano", [100_000, 700, 250])
def test_igual_con_cualquier_tamano_de_bloque(tamano):
    r = p.resumir_por_bloques(DATOS, tamano_bloque=tamano)
    for clave in CLAVES:
        if clave == "mb_totales":
            assert abs(r[clave] - ESPERADO[clave]) < 0.01
        else:
            assert r[clave] == ESPERADO[clave], f"{clave} con bloques de {tamano}: {r[clave]} != {ESPERADO[clave]}"


def test_usa_chunksize():
    texto = (Path(__file__).parent / "por_bloques.py").read_text(encoding="utf-8")
    assert "chunksize" in texto, "Lee el archivo con read_csv(..., chunksize=...)"
