"""Fixtures compartidos de tus pruebas (ejercicio m20-e8).

Define aquí, como mínimo:
  - datos_prueba (scope="session"): la carpeta tests/datos_prueba.
  - repo: un ClientesSQLite sobre un archivo .db en tmp_path, que se cierra al terminar la prueba (yield).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # para importar repositorio_sqlite
