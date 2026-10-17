"""Ejercicio m11-e7: pipeline de generadores con memoria constante.

Uso:
    python ejercicios/m11-e7/pipeline.py datos/1GB
"""

from __future__ import annotations

import sys
from pathlib import Path

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]


def resumir_cdr(ruta_cdr: Path, ruta_clientes: Path, ventana: int = 5000) -> dict:
    """Recorre el archivo UNA vez con un pipeline de generadores y devuelve un diccionario con las
    mismas claves y valores que la sección "cdr" de esperado.json para:
    registros_totales, registros_validos, errores, minutos_nacionales, minutos_internacionales,
    mb_totales y sms_totales.

    Los duplicados se detectan con una ventana de los últimos `ventana` cdr_id distintos.
    """
    raise NotImplementedError


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "datos_prueba"
    print(resumir_cdr(carpeta / "cdr.csv", carpeta / "clientes.csv"))
