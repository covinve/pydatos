"""Pruebas del ejercicio m23-e9."""

import json
from pathlib import Path

import pandas as pd
import pytest

import informe

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["facturacion"]


@pytest.fixture(scope="module")
def generado(tmp_path_factory):
    salida = tmp_path_factory.mktemp("informe") / "202609"
    return informe.generar_informe(DATOS, salida), salida


def test_resumen(generado):
    r, salida = generado
    assert r == json.loads((salida / "resumen.json").read_text(encoding="utf-8"))
    assert r["periodo"] == "202609"
    assert r["facturas"] == ESPERADO["facturas"]
    assert r["total_facturado"] == ESPERADO["total_facturado"]
    assert r["total_correcto"] == ESPERADO["total_correcto"]
    assert r["diferencia_total"] == ESPERADO["diferencia_total"]
    assert r["facturas_con_diferencia"] == ESPERADO["facturas_total_distinto"]
    assert r["cobro_de_mas"] - r["perdida"] == r["diferencia_total"]
    assert all(type(v) is int for k, v in r.items() if k != "periodo")


def test_diferencias(generado):
    r, salida = generado
    d = pd.read_csv(salida / "diferencias.csv", dtype={"linea": str})
    assert list(d.columns) == ["factura_id", "linea", "plan_id", "facturado", "correcto", "diferencia"]
    assert len(d) == r["facturas_con_diferencia"]
    assert (d["diferencia"] == d["facturado"] - d["correcto"]).all()
    assert list(d["diferencia"].abs()) == sorted(d["diferencia"].abs(), reverse=True)


def test_grafico(generado):
    _, salida = generado
    imagen = (salida / "diferencias.png").read_bytes()
    assert imagen[:8] == b"\x89PNG\r\n\x1a\n" and len(imagen) > 5_000


def test_markdown(generado):
    r, salida = generado
    texto = (salida / "informe.md").read_text(encoding="utf-8")
    assert texto.startswith("# Informe de aseguramiento de ingresos · periodo 202609")
    assert "## Resumen" in texto and "## Mayores diferencias" in texto
    assert "| Indicador | Valor |" in texto
    total = f"${r['total_facturado']:,}".replace(",", ".")
    assert total in texto, f"Los montos con formato {total}"
    assert "![Diferencias por plan](diferencias.png)" in texto
    primera = pd.read_csv(salida / "diferencias.csv", dtype=str).iloc[0]
    assert primera["factura_id"] in texto
