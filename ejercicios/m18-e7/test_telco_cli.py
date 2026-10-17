"""Pruebas del ejercicio m18-e7."""

import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import telco_cli as t

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
runner = CliRunner()


def correr(*argumentos):
    assert t.app is not None, "Crea app = typer.Typer(...)"
    return runner.invoke(t.app, [str(a) for a in argumentos])


def test_ayuda():
    r = correr("--help")
    assert r.exit_code == 0
    for comando in ("resumen", "validar", "version"):
        assert comando in r.output


def test_version():
    r = correr("version")
    assert r.exit_code == 0 and r.output.strip() == "telco-cli 1.0.0"


def test_resumen():
    r = correr("resumen", DATOS / "cdr.csv", "--tipo", "VOZ", "--top", "3")
    assert r.exit_code == 0, r.output
    esperado = [f"{l}: {n}" for l, n in t.top_lineas(DATOS / "cdr.csv", "VOZ", 3)]
    assert r.output.strip().splitlines() == esperado
    r = correr("resumen", DATOS / "cdr.csv")
    assert len(r.output.strip().splitlines()) == 5, "--top vale 5 por defecto"


@pytest.mark.parametrize("argumentos", [
    ["resumen", "no_existe.csv"],
    ["resumen", DATOS],                                   # una carpeta no es un archivo
    ["resumen", DATOS / "cdr.csv", "--tipo", "FAX"],
    ["resumen", DATOS / "cdr.csv", "--top", "0"],
    ["validar", DATOS / "cdr.csv"],                       # un archivo no es una carpeta
])
def test_errores_de_uso(argumentos):
    assert correr(*argumentos).exit_code == 2


def test_validar(tmp_path):
    salida = tmp_path / "hoy"
    r = correr("validar", DATOS, "-o", salida, "--max-rechazo", "50")
    assert r.exit_code == 0, r.output
    resumen = json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["registros_validos"] == ESPERADO["registros_validos"]
    assert resumen["errores"] == ESPERADO["errores"]
    with open(salida / "rechazos.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == sum(ESPERADO["errores"].values())
    assert set(filas[0]) == {"cdr_id", "motivo"}
    total, validos = ESPERADO["registros_totales"], ESPERADO["registros_validos"]
    porcentaje = (total - validos) / total * 100
    assert f"Válidos: {validos} de {total} ({porcentaje:.2f} % rechazados)" in r.output


def test_validar_alerta(tmp_path):
    r = correr("validar", DATOS, "--salida", tmp_path / "x", "--max-rechazo", "0.5")
    assert r.exit_code == 1
    assert "ALERTA" in r.output
    assert (tmp_path / "x" / "resumen.json").exists(), "Los archivos se escriben aunque haya alerta"


def test_validar_salida_por_defecto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = correr("validar", DATOS, "--max-rechazo", "99")
    assert r.exit_code == 0
    assert (tmp_path / "salidas" / "rechazos.csv").exists()
