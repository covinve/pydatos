"""Pruebas del ejercicio m19-e9: la conciliación como un caso de uso más de la arquitectura."""

import ast
import json
import sys
from datetime import date
from pathlib import Path

import pytest

AQUI = Path(__file__).parent
DATOS = AQUI / "datos_prueba"
PAQUETE = AQUI / "facturacion"
sys.path.insert(0, str(AQUI))

from facturacion import adaptadores_conciliacion as ac  # noqa: E402
from facturacion import conciliar as cc  # noqa: E402
from facturacion import dominio as d  # noqa: E402
from facturacion import dominio_conciliacion as dc  # noqa: E402
from facturacion.adaptadores_csv import FuenteCSV  # noqa: E402

ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["facturacion"]
ESTANDAR = {"__future__", "dataclasses", "datetime", "math", "typing", "collections", "collections.abc",
            "decimal", "enum", "functools", "itertools"}


def correcta(**cambios):
    base = dict(linea="3001", plan_id="HOG30", cargo_fijo=35900, valor_voz=5040, valor_internacional=0, valor_datos=0,
                valor_sms=0, descuento=0, subtotal=40940, iva=7779, total=48719)
    return d.Factura(**{**base, **cambios})


def emitida(**cambios):
    base = dict(factura_id="F1", linea="3001", valor_voz=5040, valor_internacional=0, valor_datos=0, valor_sms=0,
                descuento=0, subtotal=40940, iva=7779, total=48719)
    return dc.FacturaEmitida(**{**base, **cambios})


# ---------------------------------------------------------------------------
# Dominio
# ---------------------------------------------------------------------------

def test_factura_correcta_sin_hallazgos():
    assert dc.revisar(emitida(), correcta()) == []


def test_hallazgo_de_consumo():
    e = emitida(valor_datos=3000, subtotal=43940, iva=8349, total=52289)
    assert dc.revisar(e, correcta()) == [
        dc.Hallazgo("F1", "3001", "consumo", 8040, 5040),
        dc.Hallazgo("F1", "3001", "total", 52289, 48719),
    ]


def test_hallazgo_inconsistente():
    e = emitida(total=48819)
    assert dc.revisar(e, correcta()) == [
        dc.Hallazgo("F1", "3001", "inconsistente", 48819, 48719),
        dc.Hallazgo("F1", "3001", "total", 48819, 48719),
    ]


def test_resumir():
    pares = [(emitida(), correcta()),
             (emitida(factura_id="F2", valor_voz=6040, subtotal=41940, iva=7969, total=49909), correcta()),
             (emitida(factura_id="F3", total=48720), correcta())]
    assert dc.resumir(pares) == {
        "facturas": 3, "total_facturado": 48719 + 49909 + 48720, "total_correcto": 3 * 48719,
        "facturas_con_diferencia_consumo": 1, "facturas_inconsistentes": 1, "facturas_total_distinto": 2,
        "diferencia_total": 1190 + 1, "diferencia_por_consumo": 1190, "iva_correcto": 3 * 7779,
    }


# ---------------------------------------------------------------------------
# Caso de uso con dobles
# ---------------------------------------------------------------------------

PLAN = d.Plan("HOG30", 35900, 300, 15360, 100, 120, 950, 18, 60)


class FuenteMemoria:
    def planes(self):
        return {"HOG30": PLAN}

    def clientes(self):
        return [d.Cliente("3001", "HOG30", "RESIDENCIAL", date(2020, 1, 1)),
                d.Cliente("3002", "HOG30", "RESIDENCIAL", date(2020, 1, 1))]

    def cdrs(self):
        return [{"cdr_id": "1", "linea_origen": "3001", "tipo": "VOZ", "destino": "NACIONAL",
                 "fecha_inicio": "2026-09-01 10:00:00", "duracion_seg": str(342 * 60), "mb": "0"}]


class EmitidasMemoria:
    def __init__(self, facturas):
        self.facturas = facturas

    def todas(self):
        return list(self.facturas)


class SalidaMemoria:
    def __init__(self):
        self.publicado = None

    def publicar(self, resumen, hallazgos):
        self.publicado = (resumen, list(hallazgos))


def test_conciliar_con_dobles():
    emitidas = EmitidasMemoria([
        emitida(factura_id="F2", linea="3002", valor_voz=0, subtotal=35900, iva=6821, total=42721),
        emitida(factura_id="F1", linea="3001", total=48700),
    ])
    salida = SalidaMemoria()
    r = cc.conciliar(FuenteMemoria(), emitidas, salida)
    assert r["facturas"] == 2 and r["facturas_inconsistentes"] == 1 and r["diferencia_total"] == -19
    resumen, hallazgos = salida.publicado
    assert resumen == r
    assert [(h.factura_id, h.tipo) for h in hallazgos] == [("F1", "inconsistente"), ("F1", "total")]


def test_emitida_sin_cliente():
    with pytest.raises(KeyError):
        cc.conciliar(FuenteMemoria(), EmitidasMemoria([emitida(linea="9999")]), SalidaMemoria())


# ---------------------------------------------------------------------------
# De punta a punta con CSV: cuadra con esperado.json
# ---------------------------------------------------------------------------

def test_csv_cuadra_con_esperado(tmp_path):
    ruta = tmp_path / "reportes" / "conciliacion.json"
    r = cc.conciliar(FuenteCSV(DATOS), ac.EmitidasCSV(DATOS / "facturas.csv"), ac.ReporteJSON(ruta))
    assert r == ESPERADO
    reporte = json.loads(ruta.read_text(encoding="utf-8"))
    assert reporte["resumen"] == ESPERADO
    tipos = [h["tipo"] for h in reporte["hallazgos"]]
    assert tipos.count("consumo") == ESPERADO["facturas_con_diferencia_consumo"]
    assert tipos.count("total") == ESPERADO["facturas_total_distinto"]
    assert set(reporte["hallazgos"][0]) == {"factura_id", "linea", "tipo", "emitido", "correcto"}


# ---------------------------------------------------------------------------
# Arquitectura
# ---------------------------------------------------------------------------

def importa(nombre):
    arbol = ast.parse((PAQUETE / f"{nombre}.py").read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            modulos.add(f"facturacion.{nodo.module}" if nodo.level else nodo.module)
    return modulos


@pytest.mark.parametrize("modulo, permitidos", [
    ("dominio_conciliacion", ESTANDAR | {"facturacion.dominio"}),
    ("conciliar", ESTANDAR | {"facturacion.dominio", "facturacion.dominio_conciliacion", "facturacion.puertos"}),
])
def test_dependencias(modulo, permitidos):
    sobran = importa(modulo) - permitidos
    assert not sobran, f"{modulo}.py no debería importar {sobran}"


def test_no_se_modifico_la_facturacion():
    """La conciliación se AGREGA: dominio, servicios y adaptadores de facturación no cambian."""
    from facturacion import servicios
    assert hasattr(servicios, "facturar")
    assert "conciliacion" not in (PAQUETE / "dominio.py").read_text(encoding="utf-8")
