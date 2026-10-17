"""Ejercicio m23-e7: líneas sospechosas con Isolation Forest.

Uso:
    python ejercicios/m23-e7/anomalias.py datos/100MB

Funciones:

    caracteristicas(carpeta) -> pd.DataFrame
        Una fila por CADA cliente de clientes.csv (índice "linea", ordenado), también los que no tienen consumo,
        calculada sobre los CDR VÁLIDOS (las seis reglas del curso), con las columnas COLUMNAS:
            llamadas            cantidad de CDR de VOZ
            minutos             minutos facturables de VOZ ((s + 59) // 60 por llamada)
            pct_internacional   minutos internacionales / minutos (0 si no hay minutos), redondeado a 4 decimales
            pct_nocturno        proporción de llamadas de VOZ que empiezan antes de las 06:00, redondeada a 4
            mb                  MB de DATOS, redondeado a 3 decimales
            sms                 cantidad de SMS

    puntuar(df, semilla=0) -> pd.Series
        Puntaje de anomalía por línea (mismo índice): IsolationForest(n_estimators=300, random_state=semilla)
        entrenado sobre np.log1p(df[COLUMNAS]); puntaje = -score_samples (más alto = más raro).

    sospechosas(carpeta, n=10, semilla=0) -> pd.DataFrame
        Las n líneas con mayor puntaje: las COLUMNAS más "puntaje", ordenadas de mayor a menor puntaje.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

COLUMNAS = ["llamadas", "minutos", "pct_internacional", "pct_nocturno", "mb", "sms"]


if __name__ == "__main__":
    print(sospechosas(Path(sys.argv[1])))
