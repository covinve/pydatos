"""Configuración común de las pruebas del Proyecto 3."""

import json
import os
import sys
from pathlib import Path

import pytest

PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROYECTO / "src"))  # funciona aunque no hayas instalado el paquete

DATOS = PROYECTO / "datos_prueba"


@pytest.fixture(autouse=True)
def sin_variables_telco(monkeypatch):
    """Las pruebas no dependen de las variables TELCO_ definidas en tu computador."""
    for variable in list(os.environ):
        if variable.upper().startswith("TELCO_"):
            monkeypatch.delenv(variable)


@pytest.fixture(scope="session")
def carpeta_datos():
    return DATOS


@pytest.fixture(scope="session")
def esperado():
    return json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def validado(tmp_path_factory):
    """Ejecuta la validación una vez para todas las pruebas que la necesitan."""
    from telco_pipeline import validacion

    salida = tmp_path_factory.mktemp("validacion")
    return validacion.validar(DATOS, salida, memoria="500MB", hilos=2), salida
