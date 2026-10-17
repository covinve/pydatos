"""Ejercicio m16-e8: la misma pregunta con cuatro herramientas, y quién gana.

Uso:
    python ejercicios/m16-e8/comparativa.py datos/1GB
"""

from __future__ import annotations

import sys
from pathlib import Path

# Las cuatro funciones devuelven un diccionario con estas claves, calculadas sobre los CDR VÁLIDOS
# (las seis reglas del curso), iguales a la sección "cdr" de esperado.json:
CLAVES = ["registros_validos", "minutos_nacionales", "minutos_internacionales", "mb_totales", "sms_totales"]


def con_python(carpeta: Path) -> dict:
    """Python puro: csv.reader línea por línea (sin Pandas)."""
    raise NotImplementedError


def con_pandas(carpeta: Path) -> dict:
    """Pandas: read_csv completo y operaciones vectorizadas."""
    raise NotImplementedError


def con_polars(carpeta: Path) -> dict:
    """Polars en modo perezoso (scan_csv ... collect)."""
    raise NotImplementedError


def con_duckdb(carpeta: Path) -> dict:
    """DuckDB: una consulta SQL."""
    raise NotImplementedError


def medir(funcion, *argumentos) -> dict:
    """Ejecuta funcion(*argumentos) UNA vez y devuelve
    {"resultado": ..., "segundos": float, "memoria_mb": float}
    donde memoria_mb es cuánto creció la memoria del proceso (pico de RSS durante la ejecución menos
    la RSS al empezar), medida con psutil en un hilo que toma muestras cada 0.02 s.
    """
    raise NotImplementedError


if __name__ == "__main__":
    carpeta = Path(sys.argv[1])
    for funcion in (con_python, con_pandas, con_polars, con_duckdb):
        m = medir(funcion, carpeta)
        print(f"{funcion.__name__:12} {m['segundos']:8.2f} s  {m['memoria_mb']:8.0f} MB  {m['resultado']}")
