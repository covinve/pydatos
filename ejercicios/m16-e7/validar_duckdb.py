"""Ejercicio m16-e7: validar cualquier tamaño de CDR con DuckDB y guardar los válidos en Parquet.

Uso:
    python ejercicios/m16-e7/validar_duckdb.py datos/20GB salidas/20GB
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb


def procesar(carpeta: Path, salida: Path, memoria: str = "4GB") -> dict:
    """Con DuckDB (limitado a `memoria` de RAM):
      1. clasifica cada CDR con las seis reglas del curso;
      2. escribe salida/validos.parquet con los CDR válidos (todas sus columnas);
      3. escribe salida/rechazos.csv con cdr_id y motivo de los inválidos;
      4. devuelve las claves registros_totales, registros_validos, errores, minutos_nacionales,
         minutos_internacionales, mb_totales y sms_totales, iguales a esperado.json.
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(procesar(Path(sys.argv[1]), Path(sys.argv[2])))
