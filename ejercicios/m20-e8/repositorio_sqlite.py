"""El adaptador SQLite de clientes (ya está bien hecho). Ejercicio m20-e8: escribe SU suite de pruebas.

NO modifiques este archivo: la comprobación ejecuta tus pruebas contra él y contra versiones con errores.
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Cliente:
    linea: str
    nombre: str
    plan_id: str
    fecha_alta: date


class ClienteNoEncontrado(LookupError):
    pass


class ClientesSQLite:
    def __init__(self, ruta_bd: Path | str):
        self.con = sqlite3.connect(ruta_bd)
        with self.con:
            self.con.execute(
                "CREATE TABLE IF NOT EXISTS clientes (linea TEXT PRIMARY KEY, nombre TEXT, plan_id TEXT, fecha_alta TEXT)"
            )

    def cerrar(self) -> None:
        self.con.close()

    def guardar(self, c: Cliente) -> None:
        with self.con:
            self.con.execute(
                "INSERT INTO clientes VALUES (?, ?, ?, ?) ON CONFLICT (linea) DO UPDATE SET "
                "nombre = excluded.nombre, plan_id = excluded.plan_id, fecha_alta = excluded.fecha_alta",
                (c.linea, c.nombre, c.plan_id, c.fecha_alta.isoformat()),
            )

    def obtener(self, linea: str) -> Cliente:
        fila = self.con.execute("SELECT linea, nombre, plan_id, fecha_alta FROM clientes WHERE linea = ?", (linea,)).fetchone()
        if fila is None:
            raise ClienteNoEncontrado(linea)
        return Cliente(fila[0], fila[1], fila[2], date.fromisoformat(fila[3]))

    def del_plan(self, plan_id: str) -> list[Cliente]:
        filas = self.con.execute(
            "SELECT linea, nombre, plan_id, fecha_alta FROM clientes WHERE plan_id = ? ORDER BY linea", (plan_id,)
        ).fetchall()
        return [Cliente(f[0], f[1], f[2], date.fromisoformat(f[3])) for f in filas]

    def contar(self) -> int:
        return self.con.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]


def cargar_csv(repo: ClientesSQLite, ruta_csv: Path | str) -> int:
    n = 0
    with open(ruta_csv, encoding="latin-1", newline="") as f:
        for c in csv.DictReader(f):
            repo.guardar(Cliente(c["linea"], c["nombre"], c["plan_id"], date.fromisoformat(c["fecha_alta"])))
            n += 1
    return n
