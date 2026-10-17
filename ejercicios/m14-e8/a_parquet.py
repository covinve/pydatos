"""Ejercicio m14-e8: convertir un CSV de CDR en un dataset Parquet particionado por día.

Uso:
    python ejercicios/m14-e8/a_parquet.py datos/1GB/cdr.csv datos/1GB/cdr_parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

TIPOS = {"linea_origen": "string", "linea_destino": "string", "tipo": "string", "destino": "string", "celda": "string"}


def convertir(ruta_csv: Path, carpeta: Path, tamano_bloque: int = 1_000_000) -> int:
    """Lee el CSV por bloques y escribe un dataset Parquet en `carpeta`, particionado por la columna
    `dia` (texto AAAA-MM-DD tomado de fecha_inicio; si la fecha es inválida, el valor es "invalida").
    Agrega también la columna `inicio` (datetime, NaT si es inválida). Devuelve los registros escritos."""
    raise NotImplementedError


def leer_dia(carpeta: Path, dia: str, columnas: list[str] | None = None) -> pd.DataFrame:
    """Lee SOLO la partición de ese día (usa filters) y, si se indican, solo esas columnas."""
    raise NotImplementedError


if __name__ == "__main__":
    print(convertir(Path(sys.argv[1]), Path(sys.argv[2])), "registros convertidos")
