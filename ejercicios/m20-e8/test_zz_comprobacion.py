"""Comprobación automática del ejercicio m20-e8: NO modifiques este archivo.

Ejecuta TUS pruebas (tests/) contra el adaptador correcto y contra versiones con errores sembrados.
"""

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent
CORRECTO = (CARPETA / "repositorio_sqlite.py").read_text(encoding="utf-8")

MUTANTES = {
    "del_plan sin ORDER BY": CORRECTO.replace(" ORDER BY linea", " ORDER BY linea DESC"),
    "fecha_alta vuelve como texto": CORRECTO.replace(
        "return Cliente(fila[0], fila[1], fila[2], date.fromisoformat(fila[3]))", "return Cliente(*fila)"),
    "guardar no reemplaza": CORRECTO.replace(
        '"INSERT INTO clientes VALUES (?, ?, ?, ?) ON CONFLICT (linea) DO UPDATE SET "\n'
        '                "nombre = excluded.nombre, plan_id = excluded.plan_id, fecha_alta = excluded.fecha_alta"',
        '"INSERT OR IGNORE INTO clientes VALUES (?, ?, ?, ?)"'),
    "no confirma (no persiste)": CORRECTO.replace(
        "    def guardar(self, c: Cliente) -> None:\n        with self.con:\n            self.con.execute(",
        "    def guardar(self, c: Cliente) -> None:\n        if True:\n            self.con.execute("),
    "obtener devuelve None": CORRECTO.replace("            raise ClienteNoEncontrado(linea)", "            return None"),
    "cargar_csv con utf-8": CORRECTO.replace('encoding="latin-1"', 'encoding="utf-8", errors="replace"'),
    "cargar_csv cuenta mal": CORRECTO.replace("            n += 1\n    return n", "            n += 1\n    return n - 1"),
}


def correr(implementacion: str, destino: Path) -> int:
    shutil.copytree(CARPETA / "tests", destino / "tests")
    (destino / "repositorio_sqlite.py").write_text(implementacion, encoding="utf-8")
    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
        cwd=destino, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return proceso.returncode


def test_usas_conftest_y_fixtures():
    conftest = (CARPETA / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert 'scope="session"' in conftest, "Define datos_prueba con @pytest.fixture(scope=\"session\")"
    assert "yield" in conftest, "El fixture repo debe cerrar la conexión después de un yield"
    arbol = ast.parse((CARPETA / "tests" / "test_repositorio.py").read_text(encoding="utf-8"))
    pruebas = [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    assert len(pruebas) >= 6, f"Escribe al menos 6 pruebas; hay {len(pruebas)}"
    parametros = {a.arg for p in pruebas for a in p.args.args}
    assert {"repo", "datos_prueba"} <= parametros, "Usa los fixtures repo y datos_prueba en tus pruebas"


def test_pasan_con_el_correcto(tmp_path):
    assert correr(CORRECTO, tmp_path) == 0, "Tus pruebas fallan con el adaptador CORRECTO"


@pytest.mark.parametrize("error", list(MUTANTES))
def test_atrapan_el_mutante(error, tmp_path):
    assert MUTANTES[error] != CORRECTO, f"El mutante '{error}' no cambió nada (revisa la comprobación)"
    assert correr(MUTANTES[error], tmp_path) != 0, f"Tus pruebas no detectan: {error}"
