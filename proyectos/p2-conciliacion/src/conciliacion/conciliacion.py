"""Comparación entre las facturas correctas y las emitidas."""

from __future__ import annotations

import pandas as pd


def conciliar(correctas: pd.DataFrame, emitidas: pd.DataFrame) -> pd.DataFrame:
    """Solo las facturas con problemas, ordenadas por cliente_id, con las columnas
    cliente_id, factura_id, motivo, total_correcto, total_facturado, diferencia (facturado − correcto).

    motivo: "inconsistencia_interna" si en la emitida total != subtotal + iva; si no, el primer
    concepto distinto (valor_voz, valor_internacional, valor_datos, valor_sms, descuento); si no, "otro".
    """
    raise NotImplementedError


def resumen(diagnostico: pd.DataFrame, correctas: pd.DataFrame, emitidas: pd.DataFrame) -> dict:
    """Diccionario con las mismas claves y valores que la sección "facturacion" de esperado.json:
    facturas, total_facturado, total_correcto, facturas_con_diferencia_consumo, facturas_inconsistentes,
    facturas_total_distinto, diferencia_total. Además la clave "por_motivo": {motivo: {"facturas", "diferencia"}}."""
    raise NotImplementedError
