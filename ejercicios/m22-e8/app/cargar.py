"""La aplicación (ya hecha): carga clientes.csv en PostgreSQL.

    TELCO_DB_URL=postgresql+psycopg://usuario:clave@servidor:5432/base  python -m app.cargar
"""

import csv
import os
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def conectar(url: str, intentos: int = 10):
    engine = create_engine(url)
    for intento in range(intentos):
        try:
            with engine.connect() as con:
                con.execute(text("SELECT 1"))
            return engine
        except OperationalError:
            print(f"La base no responde todavía (intento {intento + 1})", flush=True)
            time.sleep(2)
    raise SystemExit("No se pudo conectar a la base de datos")


def main() -> int:
    url = os.environ.get("TELCO_DB_URL")
    if not url:
        print("Define TELCO_DB_URL", file=sys.stderr)
        return 2
    datos = Path(os.environ.get("TELCO_DATOS", "/datos"))
    with open(datos / "clientes.csv", encoding="latin-1", newline="") as f:
        clientes = [{"linea": c["linea"], "nombre": c["nombre"], "plan_id": c["plan_id"]} for c in csv.DictReader(f)]
    engine = conectar(url)
    with engine.begin() as con:
        con.execute(text("CREATE TABLE IF NOT EXISTS clientes (linea TEXT PRIMARY KEY, nombre TEXT, plan_id TEXT)"))
        con.execute(text("""
            INSERT INTO clientes VALUES (:linea, :nombre, :plan_id)
            ON CONFLICT (linea) DO UPDATE SET nombre = excluded.nombre, plan_id = excluded.plan_id
        """), clientes)
        total = con.execute(text("SELECT COUNT(*) FROM clientes")).scalar_one()
    print(f"{total} clientes cargados en PostgreSQL", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
