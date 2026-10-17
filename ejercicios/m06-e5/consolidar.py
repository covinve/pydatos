"""Ejercicio m06-e5: consolidar los archivos de roaming de una carpeta.

Uso:
    python ejercicios/m06-e5/consolidar.py CARPETA_ENTRADA ARCHIVO_SALIDA
"""

import sys
from pathlib import Path

PATRON = "cdr_*.csv"


def detectar_encoding(ruta: Path) -> str:
    """Devuelve "utf-8-sig" si el archivo empieza con BOM, "utf-8" si todo el archivo
    es UTF-8 válido, y "latin-1" en cualquier otro caso. No debe cargar el archivo completo."""
    raise NotImplementedError


def resumir_archivo(ruta: Path) -> dict:
    """Devuelve {"archivo", "registros", "minutos_voz", "encoding", "operadores"}."""
    raise NotImplementedError


def consolidar(carpeta: Path, salida: Path) -> dict:
    """Resume cada archivo cdr_*.csv de la carpeta (en orden de nombre), escribe el reporte
    y devuelve {"archivos": [...], "total_registros": int, "total_minutos_voz": int}."""
    raise NotImplementedError


if __name__ == "__main__":
    resultado = consolidar(Path(sys.argv[1]), Path(sys.argv[2]))
    for detalle in resultado["archivos"]:
        print(detalle)
    print("Total registros:", resultado["total_registros"])
