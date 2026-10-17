"""Ejercicio m19-e8: un puerto, tres adaptadores y una sola batería de pruebas de contrato."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Cliente:
    linea: str
    nombre: str
    plan_id: str
    segmento: str
    fecha_alta: date


class ClienteNoEncontrado(LookupError):
    pass


class RepositorioClientes(Protocol):
    def obtener(self, linea: str) -> Cliente:
        """El cliente de esa línea. ClienteNoEncontrado si no existe."""
        ...

    def guardar(self, cliente: Cliente) -> None:
        """Lo agrega o, si la línea ya existe, lo reemplaza."""
        ...

    def del_plan(self, plan_id: str) -> list[Cliente]:
        """Los clientes de ese plan, ordenados por línea ([] si no hay)."""
        ...

    def contar(self) -> int:
        ...


# ---------------------------------------------------------------------------
# Tu trabajo: tres implementaciones del MISMO contrato
# ---------------------------------------------------------------------------

class ClientesEnMemoria:
    """Guarda en un diccionario."""


class ClientesSQLite:
    """ClientesSQLite(ruta_bd): crea la tabla clientes si no existe (linea TEXT PRIMARY KEY, nombre, plan_id,
    segmento, fecha_alta TEXT en ISO). Los datos persisten: otra instancia sobre el mismo archivo los ve."""


class ClientesJSON:
    """ClientesJSON(ruta): un archivo JSON (utf-8, ensure_ascii=False) con una lista de clientes.
    Cada guardar() reescribe el archivo de forma segura: primero a un archivo temporal y luego
    Path.replace() sobre el definitivo. Otra instancia sobre el mismo archivo ve los datos."""


def cargar_csv(repo: RepositorioClientes, ruta_csv: Path) -> int:
    """Guarda en `repo` los clientes de un clientes.csv (latin-1) y devuelve cuántos guardó."""
    raise NotImplementedError
