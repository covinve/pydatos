"""Pruebas del ejercicio m09-e9."""

from datetime import datetime

import pytest

from tarificacion import (
    DescuentoFinDeSemana,
    DescuentoNocturno,
    Llamada,
    SinDescuento,
    Tarificador,
)

TARIFAS = {"LOCAL": 100, "NACIONAL": 120, "INTERNACIONAL": 950}
MARTES_DIA = datetime(2026, 9, 15, 14, 0)        # martes 2:00 p. m.
MARTES_NOCHE = datetime(2026, 9, 15, 23, 30)     # martes 11:30 p. m.
SABADO_DIA = datetime(2026, 9, 19, 10, 0)        # sábado 10:00 a. m.
SABADO_NOCHE = datetime(2026, 9, 19, 23, 0)


def llamada(destino="LOCAL", inicio=MARTES_DIA, segundos=125, linea="3001"):
    return Llamada(linea, destino, inicio, segundos)


def test_sin_descuento():
    assert SinDescuento().porcentaje(llamada()) == 0


def test_descuento_nocturno():
    regla = DescuentoNocturno(50)
    assert regla.porcentaje(llamada(inicio=MARTES_NOCHE)) == 50
    assert regla.porcentaje(llamada(inicio=datetime(2026, 9, 15, 5, 59))) == 50
    assert regla.porcentaje(llamada(inicio=datetime(2026, 9, 15, 6, 0))) == 0
    assert regla.porcentaje(llamada(inicio=MARTES_NOCHE, destino="INTERNACIONAL")) == 0, "No aplica a internacional"


def test_descuento_fin_de_semana():
    regla = DescuentoFinDeSemana(30)
    assert regla.porcentaje(llamada(inicio=SABADO_DIA)) == 30
    assert regla.porcentaje(llamada(inicio=datetime(2026, 9, 20, 12, 0))) == 30
    assert regla.porcentaje(llamada(inicio=MARTES_DIA)) == 0


def test_tarificar_sin_reglas():
    t = Tarificador(TARIFAS)
    assert t.tarificar(llamada()) == 300


def test_aplica_el_mejor_descuento():
    t = Tarificador(TARIFAS, [DescuentoNocturno(50), DescuentoFinDeSemana(30)])
    assert t.tarificar(llamada(inicio=SABADO_DIA)) == 210
    assert t.tarificar(llamada(inicio=SABADO_NOCHE)) == 150, "Los descuentos no se suman: se toma el mayor"


def test_redondeo_comercial():
    t = Tarificador({"LOCAL": 101}, [DescuentoNocturno(50)])
    assert t.tarificar(llamada(inicio=MARTES_NOCHE, segundos=60)) == 51


def test_destino_desconocido():
    with pytest.raises(KeyError):
        Tarificador(TARIFAS).tarificar(llamada(destino="SATELITAL"))


def test_estado_acumulado():
    t = Tarificador(TARIFAS, [DescuentoNocturno(50)])
    t.tarificar(llamada(linea="3001"))
    t.tarificar(llamada(linea="3001", inicio=MARTES_NOCHE))
    t.tarificar(llamada(linea="3002", destino="INTERNACIONAL", segundos=61))
    assert t.cantidad == 3
    assert t.total == 300 + 150 + 1900
    assert t.total_por_linea() == {"3001": 450, "3002": 1900}


def test_tarificadores_independientes():
    a, b = Tarificador(TARIFAS), Tarificador(TARIFAS)
    a.tarificar(llamada())
    assert b.total == 0 and b.cantidad == 0


def test_regla_personalizada_sin_herencia():
    class Promo:
        def porcentaje(self, llamada):
            return 100 if llamada.linea == "3999" else 0

    t = Tarificador(TARIFAS, [Promo()])
    assert t.tarificar(llamada(linea="3999")) == 0
    assert t.tarificar(llamada(linea="3001")) == 300


def test_porcentaje_invalido():
    with pytest.raises(ValueError):
        DescuentoNocturno(120)


def test_repr():
    t = Tarificador(TARIFAS, [DescuentoNocturno(50)])
    t.tarificar(llamada())
    assert repr(t) == "Tarificador(1 llamadas, total=300, reglas=[DescuentoNocturno(50)])"
