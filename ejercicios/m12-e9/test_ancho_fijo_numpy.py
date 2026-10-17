"""Pruebas del ejercicio m12-e9."""

import ast
from pathlib import Path

import numpy as np

import ancho_fijo_numpy as a

CARPETA = Path(__file__).parent
MUESTRA = CARPETA / "muestra_ancho_fijo.txt"


def test_matriz():
    m = a.leer_matriz(MUESTRA)
    assert m.dtype == np.uint8 and m.shape == (4064, 92)
    assert bytes(m[0, 35:40]) == b"DATOS"


def test_columna_entera_con_signo():
    filas = [b"000045", b"-00045", b"123456"]
    matriz = np.frombuffer(b"".join(filas), dtype=np.uint8).reshape(3, 6)
    assert a.columna_entera(matriz, 0, 6).tolist() == [45, -45, 123456]


def test_resumen_igual_al_de_python_puro():
    assert a.resumir(MUESTRA) == {
        "registros": 4064,
        "por_tipo": {"DAT": 3, "DATOS": 2647, "MMS": 4, "SMS": 189, "VOX": 4, "VOZ": 1217},
        "minutos_voz": 2910,
        "mb_datos": 145673.189,
    }


def test_sin_bucles_por_registro():
    arbol = ast.parse((CARPETA / "ancho_fijo_numpy.py").read_text(encoding="utf-8"))
    for funcion in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name in ("columna_entera", "leer_matriz")]:
        assert not any(isinstance(n, (ast.For, ast.While, ast.ListComp)) for n in ast.walk(funcion)), (
            f"{funcion.name} debe ser vectorizada"
        )
