"""Ejercicio m11-e9: dividir un archivo de CDR (normal o .gz) en partes de N registros.

Uso:
    python ejercicios/m11-e9/dividir.py datos/1GB/cdr.csv 1000000 partes/
"""

from __future__ import annotations

import sys
from pathlib import Path


def abrir_texto(ruta: Path):
    """Abre el archivo en modo texto UTF-8; si termina en .gz, lo descomprime al vuelo con gzip."""
    raise NotImplementedError


def dividir(ruta: Path, registros_por_parte: int, carpeta_salida: Path, comprimir: bool = False) -> list[Path]:
    """Divide el archivo en partes con el MISMO encabezado y como máximo `registros_por_parte`
    registros cada una. Las partes se llaman <nombre>_parte_001.csv, _parte_002.csv, ...
    (con .csv.gz si comprimir=True). Devuelve la lista de rutas creadas, en orden.
    Un archivo sin registros produce una sola parte con solo el encabezado."""
    raise NotImplementedError


if __name__ == "__main__":
    partes = dividir(Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3]))
    print(f"{len(partes)} partes creadas")
