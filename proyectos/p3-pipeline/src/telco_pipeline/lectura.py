"""Lectura de las tablas pequeñas (clientes, planes, facturas). Los CDR los lee DuckDB en validacion.py."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ARCHIVOS = ("cdr.csv", "clientes.csv", "planes.csv", "facturas.csv")


@dataclass(frozen=True)
class Tablas:
    clientes: pd.DataFrame
    planes: pd.DataFrame
    facturas: pd.DataFrame


def verificar_archivos(carpeta: Path) -> None:
    """FileNotFoundError que nombra TODOS los archivos de ARCHIVOS que faltan en la carpeta."""
    raise NotImplementedError


def leer_tablas(carpeta: Path) -> Tablas:
    """Verifica los archivos y lee clientes.csv (latin-1), planes.csv y facturas.csv.
    Las columnas linea, documento, cliente_id y periodo, como texto."""
    raise NotImplementedError
