"""Conciliación de facturas emitidas contra correctas (lógica pura)."""

from __future__ import annotations

import pandas as pd

CONCEPTOS = ["valor_voz", "valor_internacional", "valor_datos", "valor_sms"]
COLUMNAS = ["factura_id", "linea", "plan_id", "motivo", "facturado", "correcto", "diferencia"]


def conciliar(emitidas: pd.DataFrame, correctas: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Une emitidas (facturas.csv) y correctas (facturacion.facturas_correctas) por línea y devuelve:

    diferencias   las facturas cuyo total emitido difiere del correcto, con las COLUMNAS:
                  motivo = "consumo" si la suma de los CONCEPTOS emitidos difiere de la correcta;
                           si no, "inconsistente" si en la emitida total != subtotal + iva; si no, "otro".
                  diferencia = facturado − correcto. Ordenadas por |diferencia| de mayor a menor.
    resumen       las claves de la sección "facturacion" de esperado.json (como en el módulo 19, ejercicio 9).
    """
    raise NotImplementedError
