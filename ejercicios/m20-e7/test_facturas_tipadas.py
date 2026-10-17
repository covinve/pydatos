"""Pruebas del ejercicio m20-e7."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

import facturas_tipadas as f

CARPETA = Path(__file__).parent
ARCHIVO = CARPETA / "facturas_tipadas.py"


@pytest.fixture(scope="module")
def planes(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("planes") / "planes.csv"
    ruta.write_text("plan_id,cargo_fijo,minutos_incluidos,tarifa_minuto\nHOG30,35900,300,120\nILIM,89900,-1,0\n",
                    encoding="utf-8")
    return f.leer_planes(ruta)


def test_mypy_estricto():
    resultado = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "--no-incremental", "--cache-dir", os.devnull, str(ARCHIVO)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert resultado.returncode == 0, "mypy --strict encontró errores:\n" + resultado.stdout


def test_sin_trampas():
    texto = ARCHIVO.read_text(encoding="utf-8")
    assert "type: ignore" not in texto, "No silencies a mypy: corrige el error"
    arbol = ast.parse(texto)
    nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
    assert "Any" not in nombres, "No uses Any: busca el tipo preciso"


def test_tipos_de_los_planes(planes):
    assert planes["HOG30"] == f.Plan("HOG30", 35900, 300, 120)
    assert isinstance(planes["HOG30"].cargo_fijo, int)


def test_valor_voz(planes):
    assert f.valor_voz(planes, "HOG30", 342) == 5040
    assert f.valor_voz(planes, "ILIM", 9999) == 0
    with pytest.raises(f.PlanNoEncontrado):
        f.valor_voz(planes, "NOEXISTE", 10)


def test_reporte(planes):
    texto = f.reporte(planes, [("HOG30", 5040), ("ILIM", 0), ("HOG30", 1000)])
    assert texto.splitlines() == ["HOG30: $6.040 (cargo $35.900)", "ILIM: $0 (cargo $89.900)", "Promedio: $2.013"]


def test_reporte_vacio(planes):
    assert f.reporte(planes, []) == "Promedio: -"
