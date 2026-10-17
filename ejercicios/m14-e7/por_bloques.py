"""Ejercicio m14-e7: validar un CDR de cualquier tamaño con Pandas, por bloques.

Uso:
    python ejercicios/m14-e7/por_bloques.py datos/1GB 1000000
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]


def resumir_por_bloques(carpeta: Path, tamano_bloque: int = 1_000_000, ventana: int = 5000) -> dict:
    """Lee cdr.csv por bloques de `tamano_bloque` filas y devuelve las claves
    registros_totales, registros_validos, errores, minutos_nacionales, minutos_internacionales,
    mb_totales y sms_totales, iguales a esperado.json.

    Los duplicados pueden cruzar bloques: recuerda los últimos `ventana` cdr_id del bloque anterior.
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(resumir_por_bloques(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000))
