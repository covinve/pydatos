"""Configuración común de las pruebas del Proyecto 2."""

import json
import sys
from pathlib import Path

import pytest

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO / "src"))  # funciona aunque no hayas instalado el paquete

DATOS = PROYECTO / "datos_prueba"


@pytest.fixture(scope="session")
def carpeta_datos():
    return DATOS


@pytest.fixture(scope="session")
def esperado():
    return json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def datos():
    from conciliacion.lectura import leer_datos

    return leer_datos(DATOS)
