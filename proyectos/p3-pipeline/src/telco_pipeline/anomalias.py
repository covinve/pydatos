"""Líneas con comportamiento anómalo (lógica pura sobre el perfil de cada línea)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

PERFIL = ["llamadas", "minutos", "pct_internacional", "pct_nocturno", "mb", "sms"]


def puntuar(perfil: pd.DataFrame, semilla: int = 0) -> pd.Series:
    """IsolationForest(n_estimators=300, random_state=semilla) sobre np.log1p(perfil[PERFIL]);
    puntaje = -score_samples (más alto = más raro), con el mismo índice del perfil y nombre "puntaje"."""
    raise NotImplementedError


def top(perfil: pd.DataFrame, n: int = 20, semilla: int = 0) -> pd.DataFrame:
    """Las n líneas de mayor puntaje: el perfil más la columna "puntaje" (4 decimales), de mayor a menor.
    Con menos de 2 líneas no hay con qué comparar: devuelve un DataFrame vacío con esas columnas."""
    raise NotImplementedError
