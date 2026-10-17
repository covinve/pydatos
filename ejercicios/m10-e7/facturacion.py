"""Reglas de facturación del curso. NO lo modifiques: escribe sus pruebas."""

import math
from decimal import ROUND_HALF_UP, Decimal

ILIMITADO = -1
IVA = Decimal("0.19")
FECHA_CORTE_DESCUENTO = "2023-09-01"


def redondear_peso(valor) -> int:
    return int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def valor_exceso(consumido: int, incluido: int, tarifa: int) -> int:
    if incluido == ILIMITADO:
        return 0
    return max(0, consumido - incluido) * tarifa


def calcular_descuento(segmento: str, fecha_alta: str, cargo_fijo: int) -> int:
    if segmento == "EMPRESARIAL" and fecha_alta < FECHA_CORTE_DESCUENTO:
        return redondear_peso(Decimal(cargo_fijo) * Decimal("0.10"))
    return 0


def calcular_factura(cliente: dict, plan: dict, consumo: dict) -> dict:
    valor_voz = valor_exceso(consumo["minutos_nacionales"], plan["minutos_incluidos"], plan["tarifa_minuto"])
    valor_internacional = consumo["minutos_internacionales"] * plan["tarifa_minuto_internacional"]
    valor_datos = valor_exceso(math.ceil(consumo["mb"]), plan["mb_incluidos"], plan["tarifa_mb"])
    valor_sms = valor_exceso(consumo["sms"], plan["sms_incluidos"], plan["tarifa_sms"])
    adicional = valor_voz + valor_internacional + valor_datos + valor_sms
    descuento = calcular_descuento(cliente["segmento"], cliente["fecha_alta"], plan["cargo_fijo"])
    subtotal = plan["cargo_fijo"] + adicional - descuento
    iva = redondear_peso(Decimal(subtotal) * IVA)
    return {
        "valor_voz": valor_voz,
        "valor_internacional": valor_internacional,
        "valor_datos": valor_datos,
        "valor_sms": valor_sms,
        "descuento": descuento,
        "subtotal": subtotal,
        "iva": iva,
        "total": subtotal + iva,
    }
