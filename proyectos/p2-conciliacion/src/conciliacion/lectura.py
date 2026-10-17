"""Lectura de los archivos de entrada. Es el ÚNICO módulo que abre los archivos de datos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Datos:
    cdr: pd.DataFrame
    clientes: pd.DataFrame
    planes: pd.DataFrame
    facturas: pd.DataFrame


def leer_datos(carpeta: Path) -> Datos:
    """Lee cdr.csv (|), clientes.csv (latin-1), planes.csv y facturas.csv con los tipos correctos:
    identificadores (líneas, documentos) como texto y vacíos sin convertir en faltantes en el CDR.
    Lanza FileNotFoundError con un mensaje claro si falta algún archivo."""
    raise NotImplementedError
