"""Dominio: las reglas de facturación. Sin archivos, sin prints, sin csv ni pandas."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

TIPOS = ("VOZ", "SMS", "DATOS")
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
CORTE_ANTIGUEDAD = date(2023, 9, 1)
ILIMITADO = -1


@dataclass(frozen=True)
class Plan:
    plan_id: str
    cargo_fijo: int
    minutos_incluidos: int
    mb_incluidos: int
    sms_incluidos: int
    tarifa_minuto: int
    tarifa_minuto_internacional: int
    tarifa_mb: int
    tarifa_sms: int


@dataclass(frozen=True)
class Cliente:
    linea: str
    plan_id: str
    segmento: str
    fecha_alta: date


@dataclass(frozen=True)
class Consumo:
    minutos_nacionales: int = 0
    minutos_internacionales: int = 0
    mb: float = 0.0
    sms: int = 0


@dataclass(frozen=True)
class Factura:
    linea: str
    plan_id: str
    cargo_fijo: int
    valor_voz: int
    valor_internacional: int
    valor_datos: int
    valor_sms: int
    descuento: int
    subtotal: int
    iva: int
    total: int


def minutos_facturables(segundos: int) -> int:
    return (segundos + 59) // 60


def redondear(valor: float) -> int:
    return int(valor + 0.5)


def cdr_valido(cdr: dict, lineas: set[str], vistos: set[str]) -> bool:
    if cdr["cdr_id"] in vistos:
        return False
    vistos.add(cdr["cdr_id"])
    if not cdr["linea_origen"] or cdr["linea_origen"] not in lineas:
        return False
    if cdr["tipo"] not in TIPOS or int(cdr["duracion_seg"]) < 0:
        return False
    try:
        datetime.strptime(cdr["fecha_inicio"], FORMATO_FECHA)
    except ValueError:
        return False
    return True


def consumo_por_linea(cdrs: Iterable[dict], lineas: set[str]) -> dict[str, Consumo]:
    acumulado: dict[str, dict] = {}
    vistos: set[str] = set()
    for cdr in cdrs:
        if not cdr_valido(cdr, lineas, vistos):
            continue
        c = acumulado.setdefault(cdr["linea_origen"], {"nac": 0, "int": 0, "mb": 0.0, "sms": 0})
        if cdr["tipo"] == "VOZ":
            clave = "int" if cdr["destino"] == "INTERNACIONAL" else "nac"
            c[clave] += minutos_facturables(int(cdr["duracion_seg"]))
        elif cdr["tipo"] == "DATOS":
            c["mb"] += float(cdr["mb"])
        else:
            c["sms"] += 1
    return {linea: Consumo(c["nac"], c["int"], c["mb"], c["sms"]) for linea, c in acumulado.items()}


def _excedente(usado: int, incluido: int, tarifa: int) -> int:
    return 0 if incluido == ILIMITADO else max(0, usado - incluido) * tarifa


def calcular_factura(cliente: Cliente, plan: Plan, consumo: Consumo) -> Factura:
    voz = _excedente(consumo.minutos_nacionales, plan.minutos_incluidos, plan.tarifa_minuto)
    internacional = consumo.minutos_internacionales * plan.tarifa_minuto_internacional
    datos = _excedente(math.ceil(round(consumo.mb, 6)), plan.mb_incluidos, plan.tarifa_mb)
    sms = _excedente(consumo.sms, plan.sms_incluidos, plan.tarifa_sms)
    descuento = (redondear(plan.cargo_fijo * 0.10)
                 if cliente.segmento == "EMPRESARIAL" and cliente.fecha_alta < CORTE_ANTIGUEDAD else 0)
    subtotal = plan.cargo_fijo + voz + internacional + datos + sms - descuento
    iva = redondear(subtotal * 0.19)
    return Factura(cliente.linea, plan.plan_id, plan.cargo_fijo, voz, internacional, datos, sms,
                   descuento, subtotal, iva, subtotal + iva)
