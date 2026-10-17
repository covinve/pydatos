"""Pruebas del ejercicio m01-e6: ruff al rescate."""

import shutil
import subprocess
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "reporte.py"
REGLAS = ["--select", "E,F,W,N", "--line-length", "99"]


def ruff(*argumentos):
    comando = [sys.executable, "-m", "ruff", *argumentos]
    return subprocess.run(comando, cwd=CARPETA, capture_output=True, text=True, encoding="utf-8")


def test_ruff_instalado():
    proceso = ruff("--version")
    assert proceso.returncode == 0 or shutil.which("ruff"), "Instala ruff: python -m pip install -r requirements.txt"


def test_sin_problemas_de_estilo():
    proceso = ruff("check", "--no-cache", *REGLAS, str(ARCHIVO))
    assert proceso.returncode == 0, "ruff todavía encuentra problemas:\n" + proceso.stdout


def test_archivo_formateado():
    proceso = ruff("format", "--check", "--no-cache", "--line-length", "99", str(ARCHIVO))
    assert proceso.returncode == 0, "El archivo no está formateado. Ejecuta: ruff format ejercicios/m01-e6/reporte.py"


def test_las_funciones_calculan_lo_mismo():
    sys.path.insert(0, str(CARPETA))
    import reporte  # noqa: PLC0415

    assert reporte.megas_a_gigas(20480) == 20.0
    assert reporte.megas_a_gigas(512) == 0.5
    assert reporte.resumen_consumo("3001234567", 342, 20480, "HOG30") == (
        "Línea 3001234567 (HOG30): 342 min de voz y 20.0 GB de datos"
    )
    assert reporte.resumen_consumo("3109876543", 15, 512) == (
        "Línea 3109876543 (SIN PLAN): 15 min de voz y 0.5 GB de datos"
    )
