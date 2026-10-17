"""Pruebas del ejercicio m19-e7: mismo resultado que el monolito, y capas que respetan las dependencias."""

import ast
import contextlib
import io
import sys
from datetime import date
from pathlib import Path

import pytest

AQUI = Path(__file__).parent
DATOS = AQUI / "datos_prueba"
PAQUETE = AQUI / "facturacion"
sys.path.insert(0, str(AQUI))

import monolito  # noqa: E402
from facturacion import adaptadores_csv, cli, dominio, servicios  # noqa: E402

ESTANDAR = {"__future__", "dataclasses", "datetime", "math", "typing", "collections", "collections.abc",
            "decimal", "enum", "functools", "itertools"}


# ---------------------------------------------------------------------------
# Comportamiento
# ---------------------------------------------------------------------------

def test_mismo_resultado_que_el_monolito(tmp_path):
    with contextlib.redirect_stdout(io.StringIO()) as salida_monolito:
        monolito.main(DATOS, tmp_path / "monolito.csv")
    with contextlib.redirect_stdout(io.StringIO()) as salida_capas:
        codigo = cli.main([str(DATOS), str(tmp_path / "capas" / "facturas.csv")])
    assert codigo == 0
    assert (tmp_path / "capas" / "facturas.csv").read_bytes() == (tmp_path / "monolito.csv").read_bytes()
    assert salida_capas.getvalue() == salida_monolito.getvalue()


PLAN = dict(plan_id="HOG30", cargo_fijo=35900, minutos_incluidos=300, mb_incluidos=15360, sms_incluidos=100,
            tarifa_minuto=120, tarifa_minuto_internacional=950, tarifa_mb=18, tarifa_sms=60)


def test_calcular_factura_del_ejemplo():
    plan = dominio.Plan(**PLAN)
    cliente = dominio.Cliente(linea="3001112233", plan_id="HOG30", segmento="RESIDENCIAL", fecha_alta=date(2021, 1, 1))
    f = dominio.calcular_factura(cliente, plan, dominio.Consumo(minutos_nacionales=342))
    assert (f.valor_voz, f.subtotal, f.iva, f.total) == (5040, 40940, 7779, 48719)
    f = dominio.calcular_factura(cliente, plan, dominio.Consumo(mb=15360.2, sms=101, minutos_internacionales=2))
    assert (f.valor_datos, f.valor_sms, f.valor_internacional) == (18, 60, 1900)


def test_descuento_empresarial():
    plan = dominio.Plan(**{**PLAN, "cargo_fijo": 79900})
    antiguo = dominio.Cliente("3001", "HOG30", "EMPRESARIAL", date(2023, 8, 31))
    nuevo = dominio.Cliente("3002", "HOG30", "EMPRESARIAL", date(2023, 9, 1))
    assert dominio.calcular_factura(antiguo, plan, dominio.Consumo()).descuento == 7990
    assert dominio.calcular_factura(nuevo, plan, dominio.Consumo()).descuento == 0


def test_dominio_inmutable():
    with pytest.raises(Exception):
        dominio.Consumo().sms = 3


def test_consumo_por_linea_puro():
    cdrs = [
        {"cdr_id": "1", "linea_origen": "3001", "tipo": "VOZ", "destino": "NACIONAL", "fecha_inicio": "2026-09-01 10:00:00", "duracion_seg": "61", "mb": "0"},
        {"cdr_id": "1", "linea_origen": "3001", "tipo": "VOZ", "destino": "NACIONAL", "fecha_inicio": "2026-09-01 10:00:00", "duracion_seg": "61", "mb": "0"},
        {"cdr_id": "2", "linea_origen": "3001", "tipo": "DATOS", "destino": "", "fecha_inicio": "2026-09-01 11:00:00", "duracion_seg": "100", "mb": "1.5"},
        {"cdr_id": "3", "linea_origen": "9999", "tipo": "SMS", "destino": "NACIONAL", "fecha_inicio": "2026-09-01 12:00:00", "duracion_seg": "0", "mb": "0"},
    ]
    assert dominio.consumo_por_linea(cdrs, {"3001"}) == {"3001": dominio.Consumo(2, 0, 1.5, 0)}


class FuenteMemoria:
    def planes(self):
        return {"HOG30": dominio.Plan(**PLAN)}

    def clientes(self):
        return [dominio.Cliente("3001", "HOG30", "RESIDENCIAL", date(2020, 1, 1)),
                dominio.Cliente("3002", "HOG30", "RESIDENCIAL", date(2020, 1, 1))]

    def cdrs(self):
        yield {"cdr_id": "1", "linea_origen": "3001", "tipo": "VOZ", "destino": "NACIONAL",
               "fecha_inicio": "2026-09-01 10:00:00", "duracion_seg": str(342 * 60), "mb": "0"}


class SalidaMemoria:
    def __init__(self):
        self.facturas = None

    def guardar(self, facturas):
        self.facturas = list(facturas)


def test_servicio_con_dobles():
    salida = SalidaMemoria()
    r = servicios.facturar(FuenteMemoria(), salida)
    assert [f.linea for f in salida.facturas] == ["3001", "3002"]
    assert [f.total for f in salida.facturas] == [48719, 42721]
    assert r == {"facturas": 2, "total": 48719 + 42721}


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
            if nodo.level:                                   # from .dominio import X
                modulos.add(f"facturacion.{nodo.module}" if nodo.module else "facturacion")
            else:
                modulos.add(nodo.module)
    return modulos


@pytest.mark.parametrize("modulo, permitidos", [
    ("dominio", ESTANDAR),
    ("puertos", ESTANDAR | {"facturacion.dominio"}),
    ("servicios", ESTANDAR | {"facturacion.dominio", "facturacion.puertos"}),
])
def test_dependencias_hacia_adentro(modulo, permitidos):
    sobran = importa(modulo) - permitidos
    assert not sobran, f"{modulo}.py no debería importar {sobran}"


def test_adaptadores_no_conocen_el_servicio_ni_la_cli():
    malos = importa("adaptadores_csv") & {"facturacion.servicios", "facturacion.cli", "monolito"}
    assert not malos


def test_nadie_reusa_el_monolito():
    for archivo in PAQUETE.glob("*.py"):
        assert "monolito" not in archivo.read_text(encoding="utf-8"), f"{archivo.name} no debe usar monolito.py"


def test_el_servicio_no_lee_archivos():
    texto = (PAQUETE / "servicios.py").read_text(encoding="utf-8")
    assert "open(" not in texto and "print(" not in texto
