"""Pruebas del ejercicio m01-e1: entorno de trabajo listo."""

import importlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_version_de_python():
    assert sys.version_info >= (3, 11), f"Necesitas Python 3.11 o superior; tienes {sys.version.split()[0]}"


def test_dentro_de_un_entorno_virtual():
    assert sys.prefix != sys.base_prefix, (
        "No estás dentro de un entorno virtual. Actívalo con .venv\\Scripts\\Activate.ps1 "
        "o ejecuta .venv\\Scripts\\python comprobar.py m01-e1"
    )


def test_librerias_del_curso_instaladas():
    faltan = []
    for libreria in ["numpy", "pandas", "pyarrow", "polars", "duckdb", "matplotlib", "pytest", "ruff"]:
        try:
            importlib.import_module(libreria)
        except ImportError:
            faltan.append(libreria)
    assert not faltan, f"Faltan librerías: {', '.join(faltan)}. Ejecuta: python -m pip install -r requirements.txt"


def test_datos_de_10mb_generados():
    carpeta = RAIZ / "datos" / "10MB"
    assert carpeta.is_dir(), "No existe datos/10MB. Ejecuta: python herramientas/generar_datos.py --tamano 10MB"
    for archivo in ["planes.csv", "clientes.csv", "cdr.csv", "facturas.csv", "esperado.json"]:
        assert (carpeta / archivo).exists(), f"Falta datos/10MB/{archivo}: vuelve a ejecutar el generador"
    esperado = json.loads((carpeta / "esperado.json").read_text(encoding="utf-8"))
    assert esperado["cdr"]["registros_totales"] > 100_000
