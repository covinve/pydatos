"""Pruebas del ejercicio m08-e5: un paquete instalable con un comando de terminal."""

import os
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent


def test_existe_pyproject():
    assert (CARPETA / "pyproject.toml").exists(), "Crea ejercicios/m08-e5/pyproject.toml"


def test_paquete_instalado():
    try:
        version = metadata.version("telco-formato")
    except metadata.PackageNotFoundError:
        pytest.fail("El proyecto telco-formato no está instalado. Ejecuta: python -m pip install -e ejercicios/m08-e5")
    assert version == "0.1.0"


def test_instalacion_editable():
    import telco_formato

    ruta = Path(telco_formato.__file__).resolve()
    assert CARPETA / "src" in ruta.parents, (
        f"telco_formato se importa desde {ruta}; instálalo en modo editable (-e) desde esta carpeta"
    )


def test_main(monkeypatch, capsys):
    from telco_formato import cli

    monkeypatch.setattr(sys, "argv", ["telco-formato", "48719.5", "1234567"])
    cli.main()
    assert capsys.readouterr().out == "$48.720\n$1.234.567\n"


def test_comando_de_terminal():
    comando = shutil.which("telco-formato", path=os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "")]))
    assert comando, "No se encontró el comando telco-formato: revisa [project.scripts] y reinstala"
    proceso = subprocess.run([comando, "-5000"], capture_output=True, text=True, encoding="utf-8")
    assert proceso.stdout.strip() == "-$5.000"
