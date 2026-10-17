"""Pruebas del ejercicio m08-e9: paquete ejecutable con datos propios."""

import os
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
sys.path.insert(0, str(CARPETA))


def ejecutar(*argumentos, cwd=CARPETA):
    entorno = {**os.environ, "PYTHONPATH": str(CARPETA), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-m", "tarifario", *argumentos],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=entorno,
    )


def test_cargar_tarifas():
    from tarifario.calculo import cargar_tarifas

    assert cargar_tarifas() == {"LOCAL": 100, "NACIONAL": 120, "INTERNACIONAL": 950}


def test_valor():
    from tarifario.calculo import valor

    assert valor("LOCAL", 125) == 300
    assert valor("INTERNACIONAL", 61) == 1900


def test_existe_main():
    assert (CARPETA / "tarifario" / "__main__.py").exists(), "Crea tarifario/__main__.py"


def test_python_m():
    proceso = ejecutar("LOCAL", "125")
    assert proceso.returncode == 0, proceso.stderr
    assert proceso.stdout.strip() == "LOCAL · 125 s · 3 min · $300"


def test_destino_en_minusculas():
    assert ejecutar("nacional", "3600").stdout.strip() == "NACIONAL · 3600 s · 60 min · $7.200"


def test_destino_invalido():
    proceso = ejecutar("SATELITAL", "60")
    assert proceso.returncode == 2, "Con un destino inválido el programa debe terminar con código 2"
    assert "SATELITAL" in proceso.stderr, "Explica el error en stderr"
    assert proceso.stdout == ""


def test_funciona_desde_otra_carpeta(tmp_path):
    proceso = ejecutar("LOCAL", "60", cwd=tmp_path)
    assert proceso.returncode == 0, "Lee el JSON con importlib.resources, no con una ruta relativa: " + proceso.stderr
    assert proceso.stdout.strip() == "LOCAL · 60 s · 1 min · $100"
