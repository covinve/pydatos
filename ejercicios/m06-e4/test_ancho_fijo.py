"""Pruebas del ejercicio m06-e4."""

import ast
from pathlib import Path

import ancho_fijo

CARPETA = Path(__file__).parent
MUESTRA = CARPETA / "muestra_ancho_fijo.txt"


def test_registros():
    assert ancho_fijo.resumir(MUESTRA)["registros"] == 4064


def test_por_tipo():
    esperado = {"DAT": 3, "DATOS": 2647, "MMS": 4, "SMS": 189, "VOX": 4, "VOZ": 1217}
    resultado = ancho_fijo.resumir(MUESTRA)["por_tipo"]
    assert resultado == esperado
    assert list(resultado) == sorted(esperado), "Ordena el diccionario por tipo"


def test_minutos_voz():
    assert ancho_fijo.resumir(MUESTRA)["minutos_voz"] == 2910


def test_mb_datos():
    assert abs(ancho_fijo.resumir(MUESTRA)["mb_datos"] - 145673.189) < 0.001


def test_archivo_pequeno(tmp_path):
    registros = [
        "00000000000233027032633040879936   VOZ  NACIONAL     20260913103128000030000000.000CEL97932",
        "0000000000023267999245             DATOS             20260914085504001856000026.274CEL59973",
        "00000004512331234567893109876543   VOZ  LOCAL        20260901000501-00045000000.000CEL11111",
    ]
    archivo = tmp_path / "mini.txt"
    archivo.write_text("\n".join(registros) + "\n", encoding="utf-8")
    assert ancho_fijo.resumir(archivo) == {
        "registros": 3,
        "por_tipo": {"DATOS": 1, "VOZ": 2},
        "minutos_voz": 1,
        "mb_datos": 26.274,
    }


def test_no_carga_todo_el_archivo():
    arbol = ast.parse((CARPETA / "ancho_fijo.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            assert nodo.func.attr not in ("read", "readlines", "read_text"), (
                f"No uses .{nodo.func.attr}(): recorre el archivo línea por línea con for"
            )
