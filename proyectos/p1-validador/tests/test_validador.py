"""Pruebas del Proyecto 1. Ejecútalas desde la carpeta del curso con:

    python -m pytest proyectos/p1-validador -v
"""

import ast
import csv
import json
import sys
from pathlib import Path

import pytest

PROYECTO = Path(__file__).resolve().parents[1]
DATOS = PROYECTO / "datos_prueba"
sys.path.insert(0, str(PROYECTO))

import validador  # noqa: E402

ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
CLAVES = [
    "registros_totales", "registros_validos", "errores", "validos_por_tipo", "minutos_nacionales",
    "minutos_internacionales", "mb_totales", "sms_totales", "lineas_con_consumo",
]


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    salida = tmp_path_factory.mktemp("salida")
    resumen = validador.validar_archivo(DATOS / "cdr.csv", DATOS / "clientes.csv", salida)
    return resumen, salida


# --- funciones individuales ---------------------------------------------------

def test_cargar_lineas_clientes():
    lineas = validador.cargar_lineas_clientes(DATOS / "clientes.csv")
    assert isinstance(lineas, set)
    assert len(lineas) == 40
    assert all(len(l) == 10 and l.startswith("3") for l in lineas)


def fila(**cambios):
    base = {
        "cdr_id": "1", "linea_origen": "3001234567", "linea_destino": "3109876543", "tipo": "VOZ",
        "destino": "LOCAL", "fecha_inicio": "2026-09-13 10:31:28", "duracion_seg": "125", "mb": "0.000",
        "celda": "CEL1",
    }
    base.update(cambios)
    return base


CLIENTES = {"3001234567", "3109876543"}


def test_clasificar_valido():
    assert validador.clasificar(fila(), set(), CLIENTES) is None


@pytest.mark.parametrize(
    ("cambios", "esperado"),
    [
        ({"linea_origen": ""}, "linea_vacia"),
        ({"linea_origen": "3999999999"}, "linea_desconocida"),
        ({"tipo": "VOX"}, "tipo_desconocido"),
        ({"duracion_seg": "-45"}, "duracion_negativa"),
        ({"fecha_inicio": "2026-09-31 10:15:00"}, "fecha_invalida"),
        ({"fecha_inicio": "2026-09-15 25:10:00"}, "fecha_invalida"),
    ],
)
def test_clasificar_errores(cambios, esperado):
    assert validador.clasificar(fila(**cambios), set(), CLIENTES) == esperado


def test_clasificar_duplicado():
    vistos = set()
    assert validador.clasificar(fila(cdr_id="77"), vistos, CLIENTES) is None
    assert "77" in vistos, "clasificar debe agregar el cdr_id a vistos"
    assert validador.clasificar(fila(cdr_id="77"), vistos, CLIENTES) == "duplicado"


def test_orden_de_los_errores():
    assert validador.clasificar(fila(linea_origen="", tipo="VOX"), set(), CLIENTES) == "linea_vacia"


# --- archivo completo -------------------------------------------------------------

@pytest.mark.parametrize("clave", CLAVES)
def test_resumen_cuadra_con_esperado(resultado, clave):
    resumen, _ = resultado
    assert clave in resumen, f"Falta la clave {clave!r} en el resumen"
    if clave == "mb_totales":
        assert abs(resumen[clave] - ESPERADO[clave]) < 0.01
    else:
        assert resumen[clave] == ESPERADO[clave]


def test_rechazados_csv(resultado):
    _, salida = resultado
    with open(salida / "rechazados.csv", encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter="|"))
    assert len(filas) == sum(ESPERADO["errores"].values())
    assert "motivo" in filas[0] and "cdr_id" in filas[0]
    conteo = {}
    for f in filas:
        conteo[f["motivo"]] = conteo.get(f["motivo"], 0) + 1
    assert conteo == {k: v for k, v in ESPERADO["errores"].items() if v}


def test_resumen_json(resultado):
    resumen, salida = resultado
    guardado = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert guardado["registros_totales"] == resumen["registros_totales"]


def test_comparar_con_esperado(resultado):
    resumen, _ = resultado
    assert validador.comparar_con_esperado(resumen, DATOS / "esperado.json") == []
    alterado = {**resumen, "minutos_nacionales": resumen["minutos_nacionales"] + 1}
    diferencias = validador.comparar_con_esperado(alterado, DATOS / "esperado.json")
    assert len(diferencias) == 1 and "minutos_nacionales" in diferencias[0]


# --- calidad ------------------------------------------------------------------------------

def test_no_carga_el_archivo_completo():
    arbol = ast.parse((PROYECTO / "validador.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            assert nodo.func.attr not in ("read", "readlines"), f"No uses .{nodo.func.attr}(): recorre el archivo"
