"""Pruebas del ejercicio m08-e4: dividir el monolito en el paquete facturador."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).parent
PAQUETE = CARPETA / "facturador"
DATOS = CARPETA / "llamadas.csv"
sys.path.insert(0, str(CARPETA))


def salida_monolito():
    proceso = subprocess.run(
        [sys.executable, str(CARPETA / "monolito.py"), str(DATOS)],
        capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return proceso.stdout


def importar(nombre):
    if not PAQUETE.is_dir():
        pytest.fail("Crea la carpeta ejercicios/m08-e4/facturador/ con su __init__.py")
    __import__(nombre)
    return sys.modules[nombre]


def imports_de(modulo):
    arbol = ast.parse((PAQUETE / f"{modulo}.py").read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(("." * nodo.level) + (nodo.module or ""))
    return nombres


def test_estructura():
    for archivo in ["__init__.py", "lectura.py", "reglas.py", "reportes.py"]:
        assert (PAQUETE / archivo).exists(), f"Falta facturador/{archivo}"


def test_lectura_devuelve_filas():
    lectura = importar("facturador.lectura")
    filas = list(lectura.leer_cdr(DATOS))
    assert len(filas) == 9
    assert filas[0]["linea_origen"] == "3001234567"


def test_reglas():
    reglas = importar("facturador.reglas")
    assert reglas.minutos_facturables(61) == 2
    assert reglas.es_valido({"tipo": "VOZ", "duracion_seg": "60"}) is True
    assert reglas.es_valido({"tipo": "VOX", "duracion_seg": "60"}) is False
    assert reglas.es_valido({"tipo": "VOZ", "duracion_seg": "-1"}) is False


def test_reportes_resumen():
    lectura = importar("facturador.lectura")
    reportes = importar("facturador.reportes")
    resumen = reportes.resumir(lectura.leer_cdr(DATOS))
    assert resumen == {
        "validos": 7,
        "invalidos": 2,
        "minutos_por_linea": {"3001234567": 4, "3109876543": 0, "3157778899": 62},
    }


def test_mismo_texto_que_el_monolito():
    facturador = importar("facturador")
    assert facturador.procesar(DATOS) == salida_monolito().rstrip("\n")


def test_reglas_no_dependen_de_nadie():
    prohibidos = {"facturador.lectura", "facturador.reportes", ".lectura", ".reportes", "csv"}
    assert not imports_de("reglas") & prohibidos, "reglas.py no debe importar lectura, reportes ni csv"


def test_reportes_no_abren_archivos():
    texto = (PAQUETE / "reportes.py").read_text(encoding="utf-8")
    assert "open(" not in texto, "reportes.py no debe abrir archivos: recibe las filas ya leídas"
