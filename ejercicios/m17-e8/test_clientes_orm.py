"""Pruebas del ejercicio m17-e8."""

import csv
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

import clientes_orm as o

DATOS = Path(__file__).parent / "datos_prueba"
with open(DATOS / "clientes.csv", encoding="latin-1", newline="") as f:
    CLIENTES = list(csv.DictReader(f))
with open(DATOS / "planes.csv", encoding="utf-8", newline="") as f:
    PLANES = {p["plan_id"]: p for p in csv.DictReader(f)}


@pytest.fixture
def sesion():
    engine = create_engine("sqlite://")
    o.Base.metadata.create_all(engine)
    with Session(engine) as s:
        o.cargar_catalogos(s, DATOS)
        yield s


def test_cargar(sesion):
    assert sesion.scalar(select(func.count()).select_from(o.Plan)) == len(PLANES)
    assert sesion.scalar(select(func.count()).select_from(o.Cliente)) == len(CLIENTES)
    c = CLIENTES[0]
    cliente = sesion.get(o.Cliente, c["linea"])
    assert cliente.nombre == c["nombre"], "Lee clientes.csv con encoding latin-1"
    assert cliente.fecha_alta == date.fromisoformat(c["fecha_alta"])
    assert cliente.plan.cargo_fijo == int(PLANES[c["plan_id"]]["cargo_fijo"])
    assert [(h.plan_id, h.desde, h.hasta) for h in cliente.historial] == [(c["plan_id"], cliente.fecha_alta, None)]


def test_cargar_devuelve_cantidades():
    engine = create_engine("sqlite://")
    o.Base.metadata.create_all(engine)
    with Session(engine) as s:
        assert o.cargar_catalogos(s, DATOS) == (len(PLANES), len(CLIENTES))


def test_cambiar_plan(sesion):
    c = CLIENTES[1]
    nuevo = "ILIM" if c["plan_id"] != "ILIM" else "HOG60"
    o.cambiar_plan(sesion, c["linea"], nuevo, date(2026, 10, 1))
    sesion.expire_all()
    cliente = sesion.get(o.Cliente, c["linea"])
    assert cliente.plan_id == nuevo
    assert [(h.plan_id, h.hasta) for h in cliente.historial] == [(c["plan_id"], date(2026, 10, 1)), (nuevo, None)]
    assert cliente.historial[1].desde == date(2026, 10, 1)


def test_cambiar_plan_errores(sesion):
    c = CLIENTES[2]
    with pytest.raises(LookupError):
        o.cambiar_plan(sesion, "3000000000", "ILIM", date(2026, 10, 1))
    with pytest.raises(LookupError):
        o.cambiar_plan(sesion, c["linea"], "NOEXISTE", date(2026, 10, 1))
    with pytest.raises(ValueError):
        o.cambiar_plan(sesion, c["linea"], c["plan_id"], date(2026, 10, 1))
    otro = "ILIM" if c["plan_id"] != "ILIM" else "HOG60"
    with pytest.raises(ValueError):
        o.cambiar_plan(sesion, c["linea"], otro, date.fromisoformat(c["fecha_alta"]))
    sesion.expire_all()
    assert len(sesion.get(o.Cliente, c["linea"]).historial) == 1, "Los errores no deben cambiar nada"


def test_plan_vigente(sesion):
    c = CLIENTES[3]
    linea, original = c["linea"], c["plan_id"]
    alta = date.fromisoformat(c["fecha_alta"])
    otro = "ILIM" if original != "ILIM" else "HOG60"
    o.cambiar_plan(sesion, linea, otro, date(2026, 3, 1))
    o.cambiar_plan(sesion, linea, original, date(2026, 8, 15))
    assert o.plan_vigente(sesion, linea, date(alta.year - 1, 1, 1)) is None
    assert o.plan_vigente(sesion, linea, alta) == original
    assert o.plan_vigente(sesion, linea, date(2026, 2, 28)) == original
    assert o.plan_vigente(sesion, linea, date(2026, 3, 1)) == otro
    assert o.plan_vigente(sesion, linea, date(2026, 8, 14)) == otro
    assert o.plan_vigente(sesion, linea, date(2026, 8, 15)) == original
    assert o.plan_vigente(sesion, linea, date(2030, 1, 1)) == original


def test_resumen_una_consulta(sesion):
    esperado = {}
    for c in CLIENTES:
        n, total = esperado.get(c["segmento"], (0, 0))
        esperado[c["segmento"]] = (n + 1, total + int(PLANES[c["plan_id"]]["cargo_fijo"]))
    consultas = []
    event.listen(sesion.get_bind(), "before_cursor_execute", lambda *a: consultas.append(a[2]))
    r = o.resumen_por_segmento(sesion)
    assert r == [(s, *esperado[s]) for s in sorted(esperado)]
    assert len(consultas) == 1, f"Usa una sola consulta (hiciste {len(consultas)})"
