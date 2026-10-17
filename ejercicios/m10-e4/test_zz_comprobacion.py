"""Comprobación automática del ejercicio: NO modifiques este archivo.

Ejecuta TUS pruebas (test_lector.py + conftest.py) contra el lector correcto y contra
versiones con errores sembrados. Tus pruebas deben pasar con el correcto y fallar con cada mutante.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent
CORRECTO = (CARPETA / "lector.py").read_text(encoding="utf-8")

MUTANTES = {
    "cuenta el encabezado como registro": CORRECTO.replace("    registros = 0\n", "    registros = 1\n"),
    "suma minutos de duraciones negativas": CORRECTO.replace('tipo == "VOZ" and duracion >= 0', 'tipo == "VOZ"'),
    "no redondea los minutos hacia arriba": CORRECTO.replace("(duracion + 59) // 60", "duracion // 60"),
    "cuenta la línea vacía como línea": CORRECTO.replace(
        '            if campos[posicion["linea_origen"]]:\n                lineas.add', "            if True:\n                lineas.add"),
    "no ordena por_tipo": CORRECTO.replace("dict(sorted(por_tipo.items()))", "dict(por_tipo)"),
}


def correr_pruebas_del_alumno(implementacion: str, tmp_path: Path) -> int:
    for nombre in ("test_lector.py", "conftest.py"):
        shutil.copy(CARPETA / nombre, tmp_path / nombre)
    (tmp_path / "lector.py").write_text(implementacion, encoding="utf-8")
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return proceso.returncode


def test_usas_tmp_path_en_conftest():
    texto = (CARPETA / "conftest.py").read_text(encoding="utf-8")
    assert "def archivo_cdr" in texto and "tmp_path" in texto, "Crea en conftest.py la fixture archivo_cdr con tmp_path"


def test_tus_pruebas_pasan_con_el_lector_correcto(tmp_path):
    assert correr_pruebas_del_alumno(CORRECTO, tmp_path) == 0, "Tus pruebas fallan con el lector correcto"


@pytest.mark.parametrize("error", list(MUTANTES))
def test_tus_pruebas_atrapan_el_error(error, tmp_path):
    assert correr_pruebas_del_alumno(MUTANTES[error], tmp_path) == 1, f"Tus pruebas no detectan: {error}"
