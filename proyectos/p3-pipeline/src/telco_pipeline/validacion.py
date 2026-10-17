"""Validación de los CDR con DuckDB: de un CSV de cualquier tamaño a validos.parquet y rechazos.parquet.

Es el ejercicio 7 del módulo 16, con dos archivos de salida tipados.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]
FORMATO = "%Y-%m-%d %H:%M:%S"


def validar(carpeta: Path, salida: Path, memoria: str = "4GB", hilos: int = 4) -> dict:
    """Clasifica carpeta/cdr.csv con las seis reglas (en su orden de prioridad), con DuckDB limitado a
    `memoria` y `hilos`, y escribe en `salida` (la crea):

      validos.parquet    los CDR válidos, en el orden del archivo, con tipos:
                         cdr_id BIGINT, linea_origen, linea_destino, tipo, destino (texto),
                         fecha_inicio TIMESTAMP, duracion_seg INTEGER, mb DOUBLE, celda (texto)
      rechazos.parquet   fila (número de fila de datos), cdr_id, motivo

    Devuelve las claves de la sección "cdr" de esperado.json: registros_totales, registros_validos,
    errores (en el orden de ERRORES), minutos_nacionales, minutos_internacionales, mb_totales (3 decimales)
    y sms_totales.
    """
    raise NotImplementedError
