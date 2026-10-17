"""Cálculo de la factura correcta a partir del consumo válido. Funciones puras: no leen ni escriben archivos."""

from __future__ import annotations

import pandas as pd

CONCEPTOS = ["valor_voz", "valor_internacional", "valor_datos", "valor_sms", "descuento"]


def consumo_por_linea(validos: pd.DataFrame) -> pd.DataFrame:
    """Consumo de los CDR válidos, indexado por línea, con las columnas
    minutos_nacionales, minutos_internacionales, mb (suma sin redondear) y sms."""
    raise NotImplementedError


def facturas_correctas(clientes: pd.DataFrame, planes: pd.DataFrame, consumo: pd.DataFrame) -> pd.DataFrame:
    """Una fila por cliente (también sin consumo) con las columnas
    cliente_id, cargo_fijo, valor_voz, valor_internacional, valor_datos, valor_sms, descuento, subtotal, iva, total
    (todas enteras), según las reglas de facturación del curso."""
    raise NotImplementedError
