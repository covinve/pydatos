"""Ejercicio m15-e9: reporte exploratorio automático.

Uso:
    python ejercicios/m15-e9/reporte_eda.py datos/10MB reportes/eda_10MB
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # genera imágenes sin abrir ventanas

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def generar_reporte(carpeta_datos: Path, carpeta_salida: Path) -> dict:
    """Lee cdr.csv, clientes.csv y planes.csv de carpeta_datos y crea en carpeta_salida:

    - registros_por_dia.png, duracion_llamadas.png, consumo_por_plan.png y mapa_dia_hora.png
    - reporte.md: título, una sección por gráfico con la imagen (![...](archivo.png)) y una
      frase con un dato concreto, más una tabla con los indicadores del diccionario devuelto.

    Devuelve un diccionario de indicadores (sobre los CDR VÁLIDOS según las reglas del curso):
      registros            total de CDR del archivo
      validos              CDR válidos
      pct_validos          porcentaje de válidos, 1 decimal
      minutos              minutos facturables de voz (nacionales + internacionales)
      gb                   megas de datos / 1024, 2 decimales
      hora_pico            hora (0-23) con más llamadas de voz válidas; en empate, la más temprana
      mediana_duracion_seg mediana de la duración de las llamadas de voz válidas con duración > 0 (float)
      clientes_sin_consumo clientes sin ningún CDR válido
    """
    raise NotImplementedError


if __name__ == "__main__":
    print(generar_reporte(Path(sys.argv[1]), Path(sys.argv[2])))
