"""Comprobación automática del ejercicio: NO modifiques este archivo."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent
CORRECTO = (CARPETA / "proceso.py").read_text(encoding="utf-8")

MUTANTES = {
    "ignora la variable de entorno": CORRECTO.replace('os.environ.get("CARPETA_CDR", "entrada")', '"entrada"'),
    "cuenta el encabezado": CORRECTO.replace("sum(1 for _ in archivo) - 1", "sum(1 for _ in archivo)"),
    "no advierte los archivos vacíos": CORRECTO.replace('            log.warning("Archivo vacío: %s", ruta.name)\n', "            pass\n"),
    "imprime mal el total": CORRECTO.replace('print(f"Total: {total} registros")', 'print(f"Total {total}")'),
    "no respeta --minimo": CORRECTO.replace("    if total < minimo:", "    if False:"),
    "código de salida incorrecto sin carpeta": CORRECTO.replace("        return 2\n", "        return 1\n"),
    "procesa archivos que no son cdr_*.csv": CORRECTO.replace('carpeta.glob("cdr_*.csv")', 'carpeta.glob("*.csv")'),
}


def correr(implementacion: str, carpeta: Path) -> int:
    for nombre in ("test_proceso.py", "conftest.py"):
        if (CARPETA / nombre).exists():
            shutil.copy(CARPETA / nombre, carpeta / nombre)
    (carpeta / "proceso.py").write_text(implementacion, encoding="utf-8")
    entorno = {k: v for k, v in os.environ.items() if k != "CARPETA_CDR"}
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_proceso.py"],
        cwd=carpeta, capture_output=True, text=True, encoding="utf-8", env={**entorno, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return proceso.returncode


def test_usas_las_herramientas():
    texto = (CARPETA / "test_proceso.py").read_text(encoding="utf-8")
    for herramienta in ("monkeypatch", "capsys", "caplog", "tmp_path"):
        assert herramienta in texto, f"Usa la fixture {herramienta} en tus pruebas"


def test_pasan_con_el_codigo_correcto(tmp_path):
    assert correr(CORRECTO, tmp_path) == 0, "Tus pruebas fallan con el código correcto"


@pytest.mark.parametrize("error", list(MUTANTES))
def test_atrapan_el_mutante(error, tmp_path):
    assert correr(MUTANTES[error], tmp_path) == 1, f"Tus pruebas no detectan: {error}"
