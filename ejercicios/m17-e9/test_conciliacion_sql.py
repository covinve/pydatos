"""Pruebas del ejercicio m17-e9."""

import os
import re
from pathlib import Path

import pandas as pd
import pytest

import conciliacion_sql as c

DATOS = Path(__file__).parent / "datos_prueba"
COLUMNAS = ["factura_id", "linea", "voz_facturado", "voz_calculado", "internacional_facturado",
            "internacional_calculado", "diferencia"]


def esperado(periodo):
    v = c._cdr_validos(DATOS)
    v = v[v["tipo"] == "VOZ"].assign(m=lambda d: (d["duracion_seg"] + 59) // 60,
                                      inter=lambda d: d["destino"] == "INTERNACIONAL")
    nac = v[~v["inter"]].groupby("linea_origen")["m"].sum()
    inter = v[v["inter"]].groupby("linea_origen")["m"].sum()
    planes = pd.read_csv(DATOS / "planes.csv").set_index("plan_id")
    filas = []
    for f in pd.read_csv(DATOS / "facturas.csv", dtype={"linea": str}).itertuples():
        if f.periodo != periodo:
            continue
        p = planes.loc[f.plan_id]
        voz = 0 if p.minutos_incluidos == -1 else max(0, int(nac.get(f.linea, 0)) - p.minutos_incluidos) * p.tarifa_minuto
        inte = int(inter.get(f.linea, 0)) * p.tarifa_minuto_internacional
        dif = voz + inte - f.valor_voz - f.valor_internacional
        if dif:
            filas.append((f.factura_id, f.linea, f.valor_voz, voz, f.valor_internacional, inte, dif))
    return sorted(filas)


def comparar(engine):
    c.cargar(engine, DATOS)
    r = c.diferencias_voz(engine, 202609)
    assert list(r.columns) == COLUMNAS
    obtenido = [(str(f[0]), str(f[1]), *(int(x) for x in f[2:])) for f in r.itertuples(index=False)]
    e = [(a, b, *(int(x) for x in resto)) for a, b, *resto in esperado(202609)]
    assert obtenido == e


def test_en_sqlite():
    comparar(c.crear_engine("sqlite://"))


def test_otro_periodo_vacio():
    engine = c.crear_engine("sqlite://")
    c.cargar(engine, DATOS)
    assert len(c.diferencias_voz(engine, 199901)) == 0


def test_hay_diferencias():
    assert esperado(202609), "Los datos de prueba deben tener al menos una diferencia"


def test_sql_portable():
    sql = c.SQL_DIFERENCIAS.upper()
    assert ":PERIODO" in sql, "Usa el parámetro :periodo"
    for prohibido in ("IFNULL", "STRFTIME", "IIF("):
        assert prohibido not in sql, f"{prohibido} es propio de SQLite: usa una alternativa estándar"
    assert not re.search(r"\b(MAX|MIN)\s*\([^()]*,", sql), "MAX(a, b) es propio de SQLite: usa CASE WHEN"


@pytest.mark.skipif("TELCO_DB_URL_PRUEBAS" not in os.environ, reason="Sin PostgreSQL (módulo 22)")
def test_en_postgresql():
    comparar(c.crear_engine(os.environ["TELCO_DB_URL_PRUEBAS"]))
