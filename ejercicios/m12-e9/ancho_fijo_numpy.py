"""Ejercicio m12-e9: resumir un archivo de ancho fijo con np.memmap, sin bucles por registro.

Uso:
    python ejercicios/m12-e9/ancho_fijo_numpy.py datos/1GB/cdr_ancho_fijo.txt
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ANCHO = 92  # 91 caracteres + salto de línea


def leer_matriz(ruta: Path) -> np.ndarray:
    """Devuelve una matriz de bytes (uint8) de forma (registros, 92) usando np.memmap."""
    raise NotImplementedError


def columna_entera(matriz: np.ndarray, inicio: int, fin: int) -> np.ndarray:
    """Convierte las posiciones [inicio, fin) de cada registro (dígitos ASCII, con un posible
    signo '-' en la primera posición) a un array int64, sin bucles por registro."""
    raise NotImplementedError


def resumir(ruta: Path) -> dict:
    """Mismo resultado que el ejercicio m06-e4:
    {"registros", "por_tipo", "minutos_voz", "mb_datos"} (por_tipo ordenado por tipo)."""
    raise NotImplementedError


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "muestra_ancho_fijo.txt"
    inicio = time.perf_counter()
    resultado = resumir(ruta)
    print(resultado)
    print(f"{ruta.stat().st_size / 1e6:,.0f} MB en {time.perf_counter() - inicio:.2f} s")
