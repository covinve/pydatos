"""Reglas de validación de los CDR (ver Referencia → Datos del curso)."""

from __future__ import annotations

import pandas as pd

PRIORIDAD = ["duplicado", "linea_vacia", "linea_desconocida", "tipo_desconocido", "duracion_negativa", "fecha_invalida"]


def clasificar(cdr: pd.DataFrame, clientes: pd.DataFrame) -> pd.Series:
    """Devuelve, alineada con `cdr`, el primer error de cada registro según PRIORIDAD, o "valido"."""
    raise NotImplementedError
