"""Comprobación automática del ejercicio: NO modifiques este archivo."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent
CORRECTO = (CARPETA / "facturacion.py").read_text(encoding="utf-8")

MUTANTES = {
    "IVA con round() del banquero": CORRECTO.replace(
        "    return int(Decimal(str(valor)).quantize(Decimal(\"1\"), rounding=ROUND_HALF_UP))", "    return round(valor)"),
    "el ilimitado cobra exceso": CORRECTO.replace("    if incluido == ILIMITADO:\n        return 0\n", ""),
    "descuento con <= en la fecha de corte": CORRECTO.replace("fecha_alta < FECHA_CORTE_DESCUENTO", "fecha_alta <= FECHA_CORTE_DESCUENTO"),
    "descuento también para residenciales": CORRECTO.replace('segmento == "EMPRESARIAL" and ', ""),
    "megas sin redondear hacia arriba": CORRECTO.replace("math.ceil(consumo[\"mb\"])", "int(consumo[\"mb\"])"),
    "olvida el consumo internacional": CORRECTO.replace(
        "valor_voz + valor_internacional + valor_datos", "valor_voz + valor_datos"),
    "SMS con la tarifa de minutos": CORRECTO.replace('plan["tarifa_sms"])', 'plan["tarifa_minuto"])'),
}


def correr(implementacion: str, carpeta: Path, *opciones: str) -> subprocess.CompletedProcess:
    shutil.copy(CARPETA / "test_facturacion.py", carpeta / "test_facturacion.py")
    if (CARPETA / "conftest.py").exists():
        shutil.copy(CARPETA / "conftest.py", carpeta / "conftest.py")
    (carpeta / "facturacion.py").write_text(implementacion, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *opciones, "test_facturacion.py"],
        cwd=carpeta, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_pasan_y_cobertura_completa(tmp_path):
    proceso = correr(CORRECTO, tmp_path, "--cov=facturacion", "--cov-branch", "--cov-report=json:cobertura.json")
    assert proceso.returncode == 0, "Tus pruebas fallan con el código correcto:\n" + proceso.stdout[-1500:]
    datos = json.loads((tmp_path / "cobertura.json").read_text(encoding="utf-8"))
    porcentaje = datos["totals"]["percent_covered"]
    faltan = datos["files"]["facturacion.py"]["missing_lines"]
    assert porcentaje >= 100, f"Cobertura de {porcentaje:.0f} %. Líneas sin ejecutar: {faltan}"


@pytest.mark.parametrize("error", list(MUTANTES))
def test_atrapan_el_mutante(error, tmp_path):
    assert correr(MUTANTES[error], tmp_path).returncode == 1, f"Tus pruebas no detectan: {error}"
