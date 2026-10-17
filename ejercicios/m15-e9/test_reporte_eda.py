"""Pruebas del ejercicio m15-e9."""

import json
from pathlib import Path

import pandas as pd
import pytest

import reporte_eda as r

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
IMAGENES = ["registros_por_dia.png", "duracion_llamadas.png", "consumo_por_plan.png", "mapa_dia_hora.png"]


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    salida = tmp_path_factory.mktemp("eda")
    return r.generar_reporte(DATOS, salida), salida


def test_indicadores(resultado):
    ind, _ = resultado
    assert ind["registros"] == ESPERADO["registros_totales"]
    assert ind["validos"] == ESPERADO["registros_validos"]
    assert ind["pct_validos"] == round(ESPERADO["registros_validos"] / ESPERADO["registros_totales"] * 100, 1)
    assert ind["minutos"] == ESPERADO["minutos_nacionales"] + ESPERADO["minutos_internacionales"]
    assert ind["gb"] == round(ESPERADO["mb_totales"] / 1024, 2)
    llamadas_hora = ESPERADO["llamadas_por_hora"]
    assert ind["hora_pico"] == int(max(llamadas_hora, key=lambda h: (llamadas_hora[h], -int(h))))
    clientes = pd.read_csv(DATOS / "clientes.csv", encoding="latin-1")
    assert ind["clientes_sin_consumo"] == len(clientes) - ESPERADO["lineas_con_consumo"]
    assert isinstance(ind["mediana_duracion_seg"], float)


def test_imagenes(resultado):
    _, salida = resultado
    for nombre in IMAGENES:
        ruta = salida / nombre
        assert ruta.exists(), f"Falta {nombre}"
        assert ruta.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"{nombre} no es un PNG válido"


def test_reporte_markdown(resultado):
    ind, salida = resultado
    texto = (salida / "reporte.md").read_text(encoding="utf-8")
    assert texto.startswith("# "), "El reporte debe empezar con un título"
    for nombre in IMAGENES:
        assert f"]({nombre})" in texto, f"El reporte debe incluir la imagen {nombre}"
    assert texto.count("\n## ") >= 4, "Incluye una sección por gráfico"
    assert str(ind["validos"]) in texto.replace(".", "") or f"{ind['validos']:,}".replace(",", ".") in texto
