"""Ejercicio m18-e7: la CLI del equipo de facturación, con Typer.

Uso (cuando la termines):
    python ejercicios/m18-e7/telco_cli.py --help
    python ejercicios/m18-e7/telco_cli.py resumen datos/10MB/cdr.csv --tipo VOZ --top 3
    python ejercicios/m18-e7/telco_cli.py validar datos/10MB --salida salidas/hoy --max-rechazo 2.5
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

__version__ = "1.0.0"
ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]


# ---------------------------------------------------------------------------
# Lógica (ya está hecha: la CLI solo la usa)
# ---------------------------------------------------------------------------

def motivo(fila: dict, vistos: set, clientes: set) -> str:
    if fila["cdr_id"] in vistos:
        return "duplicado"
    vistos.add(fila["cdr_id"])
    if not fila["linea_origen"]:
        return "linea_vacia"
    if fila["linea_origen"] not in clientes:
        return "linea_desconocida"
    if fila["tipo"] not in ("VOZ", "SMS", "DATOS"):
        return "tipo_desconocido"
    if int(fila["duracion_seg"]) < 0:
        return "duracion_negativa"
    try:
        datetime.strptime(fila["fecha_inicio"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return "fecha_invalida"
    return "valido"


def validar_cdr(carpeta: Path) -> tuple[dict, list[tuple[str, str]]]:
    """Devuelve (resumen, rechazos): resumen con registros_totales, registros_validos y errores;
    rechazos como lista de (cdr_id, motivo)."""
    with open(carpeta / "clientes.csv", encoding="latin-1", newline="") as f:
        clientes = {c["linea"] for c in csv.DictReader(f)}
    vistos: set = set()
    conteo: Counter = Counter()
    rechazos = []
    with open(carpeta / "cdr.csv", encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f, delimiter="|"):
            m = motivo(fila, vistos, clientes)
            conteo[m] += 1
            if m != "valido":
                rechazos.append((fila["cdr_id"], m))
    resumen = {
        "registros_totales": sum(conteo.values()),
        "registros_validos": conteo["valido"],
        "errores": {e: conteo[e] for e in ERRORES},
    }
    return resumen, rechazos


def top_lineas(archivo: Path, tipo: str | None, top: int) -> list[tuple[str, int]]:
    conteo: Counter = Counter()
    with open(archivo, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f, delimiter="|"):
            if fila["linea_origen"] and (tipo is None or fila["tipo"] == tipo):
                conteo[fila["linea_origen"]] += 1
    return sorted(conteo.items(), key=lambda par: (-par[1], par[0]))[:top]


# ---------------------------------------------------------------------------
# Tu trabajo: la CLI
# ---------------------------------------------------------------------------
#
# app = typer.Typer(...) con tres comandos:
#
#   resumen ARCHIVO [--tipo VOZ|SMS|DATOS] [--top N]
#       ARCHIVO debe existir y ser un archivo (si no, Typer termina con código 2).
#       --top: entero >= 1, por defecto 5. --tipo: solo VOZ, SMS o DATOS (usa un Enum).
#       Imprime una línea por resultado de top_lineas con el formato "3001112233: 12".
#
#   validar CARPETA [--salida/-o DIR] [--max-rechazo PORCENTAJE]
#       CARPETA debe existir y ser una carpeta. --salida por defecto "salidas". --max-rechazo por defecto 5.0.
#       Crea DIR y escribe DIR/resumen.json (el resumen, indentado) y DIR/rechazos.csv (cdr_id,motivo con cabecera).
#       Imprime "Válidos: N de M (P % rechazados)" con P con 2 decimales.
#       Si P supera --max-rechazo, imprime "ALERTA: ..." y termina con código 1; si no, código 0.
#
#   version
#       Imprime "telco-cli 1.0.0".

app = None


if __name__ == "__main__":
    app()
