"""Pruebas del ejercicio m07-e5."""

from pathlib import Path

import tarificador as t

LINEAS = (Path(__file__).parent / "llamadas.csv").read_text(encoding="utf-8").splitlines()
ESPERADO = {"3001234567": 420, "3109876543": 0, "3157778899": 9100}


def test_minutos_facturables():
    assert t.minutos(0) == 0, "Una llamada de 0 segundos no se cobra"
    assert t.minutos(1) == 1
    assert t.minutos(60) == 1, "60 segundos son exactamente 1 minuto"
    assert t.minutos(61) == 2
    assert t.minutos(3600) == 60


def test_tarifa_por_destino():
    assert t.tarifa("LOCAL", t.TARIFAS) == 100
    assert t.tarifa("INTERNACIONAL", t.TARIFAS) == 950


def test_valor_por_linea():
    assert t.valor_por_linea(LINEAS, t.TARIFAS) == ESPERADO


def test_llamadas_independientes():
    t.valor_por_linea(LINEAS, t.TARIFAS)
    assert t.valor_por_linea(LINEAS, t.TARIFAS) == ESPERADO, "La segunda llamada no debe arrastrar valores de la primera"
