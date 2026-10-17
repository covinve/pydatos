"""Consumo y perfil por línea a partir de validos.parquet (con DuckDB: no cargues los CDR en memoria)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

PERFIL = ["llamadas", "minutos", "pct_internacional", "pct_nocturno", "mb", "sms"]


def consumo_por_linea(validos: Path) -> pd.DataFrame:
    """Una fila por línea con consumo (índice "linea", ordenado) y las columnas
    minutos_nacionales, minutos_internacionales (enteros, facturables por llamada), mb (suma SIN redondear) y sms."""
    raise NotImplementedError


def perfil_lineas(validos: Path) -> pd.DataFrame:
    """Una fila por línea con consumo (índice "linea", ordenado) y las columnas PERFIL:
    llamadas (VOZ), minutos, pct_internacional (minutos internacionales / minutos, 4 decimales),
    pct_nocturno (llamadas antes de las 06:00 / llamadas, 4 decimales), mb (3 decimales) y sms.
    Es el perfil del ejercicio 7 del módulo 23."""
    raise NotImplementedError
