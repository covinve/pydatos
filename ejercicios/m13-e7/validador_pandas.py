"""Ejercicio m13-e7: validador completo con Pandas que escribe sus reportes.

Uso:
    python ejercicios/m13-e7/validador_pandas.py datos/10MB reportes/pandas
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


def leer(carpeta: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee cdr.csv y clientes.csv de la carpeta con los tipos correctos."""
    raise NotImplementedError


def clasificar(cdr: pd.DataFrame, clientes: pd.DataFrame) -> pd.Series:
    """Primer error de cada registro (reglas del curso) o "valido"."""
    raise NotImplementedError


def resumen(cdr: pd.DataFrame, clasificacion: pd.Series) -> dict:
    """Mismas claves y valores que la sección "cdr" de esperado.json para:
    registros_totales, registros_validos, errores, validos_por_tipo, minutos_nacionales,
    minutos_internacionales, mb_totales, sms_totales y lineas_con_consumo."""
    raise NotImplementedError


def validar(carpeta: Path, salida: Path) -> dict:
    """Lee, clasifica, escribe salida/rechazados.csv (con columna motivo, separado por |)
    y salida/resumen.json, y devuelve el resumen."""
    raise NotImplementedError


if __name__ == "__main__":
    print(validar(Path(sys.argv[1]), Path(sys.argv[2])))
