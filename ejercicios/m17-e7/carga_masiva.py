"""Ejercicio m17-e7: carga masiva de CDR a SQLite, con validación en SQL, rechazos e idempotencia.

Uso:
    python ejercicios/m17-e7/carga_masiva.py datos/100MB salidas/telco.db
"""

from __future__ import annotations

import sys
from pathlib import Path

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]
COLUMNAS = ["cdr_id", "linea_origen", "linea_destino", "tipo", "destino", "fecha_inicio", "duracion_seg", "mb", "celda"]


def cargar_cdr(carpeta: Path, ruta_bd: Path, lote: int = 100_000) -> dict:
    """Carga carpeta/cdr.csv en la base SQLite ruta_bd.

    1. Crea, si no existen, las tablas:
       - clientes (linea TEXT PRIMARY KEY, plan_id TEXT): se llena (o actualiza) con carpeta/clientes.csv.
       - paso_cdr: las 9 columnas del CSV como TEXT, más fila INTEGER (número de fila de datos, desde 1).
       - cdr: cdr_id INTEGER PRIMARY KEY, las otras 8 columnas (duracion_seg INTEGER, mb REAL, el resto TEXT)
         y archivo TEXT.
       - rechazos: archivo TEXT, fila INTEGER, cdr_id TEXT, motivo TEXT, PRIMARY KEY (archivo, fila).
    2. Vacía paso_cdr y la llena leyendo el CSV con csv.reader en lotes de `lote` filas (executemany,
       una transacción por lote).
    3. Con SQL, clasifica cada fila de paso_cdr con las seis reglas del curso (en su orden de prioridad),
       copia los válidos a cdr y los inválidos a rechazos (INSERT OR IGNORE: la carga es repetible).
    4. Crea, si no existen, los índices ix_cdr_linea (cdr.linea_origen) e ix_cdr_fecha (cdr.fecha_inicio),
       y vacía paso_cdr.

    Devuelve {"leidos": n, "validos": n, "rechazados": n, "errores": {error: n, ...}} (en el orden de ERRORES)
    con lo clasificado en ESTA carga.
    """
    raise NotImplementedError


if __name__ == "__main__":
    import time

    inicio = time.perf_counter()
    print(cargar_cdr(Path(sys.argv[1]), Path(sys.argv[2])))
    print(f"{time.perf_counter() - inicio:.1f} s")
