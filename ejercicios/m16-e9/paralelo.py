"""Ejercicio m16-e9: procesar una carpeta de archivos diarios usando todos los núcleos.

Uso:
    python ejercicios/m16-e9/paralelo.py carpeta_con_archivos_diarios
"""

from __future__ import annotations

import sys
from pathlib import Path


def resumir_archivo(ruta: Path) -> dict:
    """Resume UN archivo de CDR (mismo formato que cdr.csv) con csv.reader y devuelve:
    {"archivo": nombre, "registros": total de filas,
     "por_tipo": {"VOZ": n, "SMS": n, "DATOS": n},      # solo esos tres tipos
     "minutos": minutos facturables de VOZ con duración >= 0,
     "mb": MB de DATOS, redondeado a 3 decimales}
    """
    raise NotImplementedError


def combinar(resumenes: list[dict]) -> dict:
    """Suma varios resúmenes en uno con las claves archivos (cantidad), registros, por_tipo, minutos y mb."""
    raise NotImplementedError


def secuencial(carpeta: Path) -> dict:
    """Resume todos los cdr_*.csv de la carpeta, uno tras otro, y los combina."""
    raise NotImplementedError


def en_paralelo(carpeta: Path, procesos: int | None = None) -> dict:
    """Igual que secuencial, pero con concurrent.futures.ProcessPoolExecutor(max_workers=procesos)."""
    raise NotImplementedError


if __name__ == "__main__":
    import time

    carpeta = Path(sys.argv[1])
    for funcion in (secuencial, en_paralelo):
        inicio = time.perf_counter()
        r = funcion(carpeta)
        print(f"{funcion.__name__:12} {time.perf_counter() - inicio:6.2f} s  {r}")
