"""Reglas de facturación (lógica pura: recibe y devuelve DataFrames, no lee ni escribe archivos).

Las reglas están en la página de referencia "Datos del curso" (las mismas del proyecto 2).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CORTE_ANTIGUEDAD = "2023-09-01"
COLUMNAS = ["linea", "cliente_id", "plan_id", "segmento", "cargo_fijo", "valor_voz", "valor_internacional",
            "valor_datos", "valor_sms", "descuento", "subtotal", "iva", "total"]


def redondear(valores) -> np.ndarray:
    """Al peso más cercano; 0,5 sube. Devuelve enteros (int64)."""
    raise NotImplementedError


def excedente(usado, incluido, tarifa) -> np.ndarray:
    """max(0, usado − incluido) × tarifa, elemento a elemento; 0 si el plan es ilimitado (incluido = −1)."""
    raise NotImplementedError


def facturas_correctas(clientes: pd.DataFrame, planes: pd.DataFrame, consumo: pd.DataFrame) -> pd.DataFrame:
    """Una fila por cliente (también los que no tienen consumo) con las COLUMNAS, todas enteras salvo las de texto.
    `consumo` es el resultado de consumo.consumo_por_linea (índice "linea")."""
    raise NotImplementedError
