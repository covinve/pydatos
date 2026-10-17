"""Ejercicio m17-e9: conciliar la voz facturada con SQL portable (SQLite hoy, PostgreSQL mañana).

Uso:
    python ejercicios/m17-e9/conciliacion_sql.py datos/10MB 202609
    TELCO_DB_URL=postgresql+psycopg://... python ejercicios/m17-e9/conciliacion_sql.py datos/10MB 202609
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, create_engine, text


def crear_engine(url: str | None = None) -> Engine:
    """Engine para `url`, o para la variable de entorno TELCO_DB_URL, o SQLite en memoria."""
    return create_engine(url or os.environ.get("TELCO_DB_URL", "sqlite://"))


def _cdr_validos(carpeta: Path) -> pd.DataFrame:
    """Los CDR válidos con las seis reglas del curso (ya lo sabes hacer: módulo 13)."""
    cdr = pd.read_csv(carpeta / "cdr.csv", sep="|", dtype=str, keep_default_na=False)
    lineas = pd.read_csv(carpeta / "clientes.csv", encoding="latin-1", dtype=str)["linea"]
    duracion = pd.to_numeric(cdr["duracion_seg"])
    fecha = pd.to_datetime(cdr["fecha_inicio"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    ok = (~cdr["cdr_id"].duplicated() & cdr["linea_origen"].isin(lineas)
          & cdr["tipo"].isin(["VOZ", "SMS", "DATOS"]) & (duracion >= 0) & fecha.notna())
    validos = cdr[ok].copy()
    validos["duracion_seg"] = duracion[ok].astype("int64")
    validos["mb"] = pd.to_numeric(validos["mb"])
    return validos


def cargar(engine: Engine, carpeta: Path) -> None:
    """Crea las tablas planes, facturas y cdr (solo los válidos). Ya está hecho."""
    carpeta = Path(carpeta)
    planes = pd.read_csv(carpeta / "planes.csv")
    facturas = pd.read_csv(carpeta / "facturas.csv", dtype={"linea": str})
    with engine.begin() as con:
        planes.to_sql("planes", con, index=False, if_exists="replace")
        facturas.to_sql("facturas", con, index=False, if_exists="replace")
        _cdr_validos(carpeta).to_sql("cdr", con, index=False, if_exists="replace", chunksize=50_000)


# ---------------------------------------------------------------------------
# Tu trabajo
# ---------------------------------------------------------------------------

# Una consulta SQL PORTABLE (sin funciones propias de SQLite como MAX(a, b), IFNULL o strftime)
# con un parámetro :periodo. Para cada factura de ese periodo devuelve las columnas
#   factura_id, linea, voz_facturado, voz_calculado, internacional_facturado, internacional_calculado, diferencia
# donde:
#   voz_calculado = excedente de minutos nacionales sobre minutos_incluidos × tarifa_minuto (0 si el plan es -1)
#   internacional_calculado = minutos internacionales × tarifa_minuto_internacional
#   diferencia = (voz_calculado + internacional_calculado) - (voz_facturado + internacional_facturado)
# Solo las facturas con diferencia distinta de 0, ordenadas por factura_id.
# Una línea sin CDR tiene 0 minutos.
SQL_DIFERENCIAS = """
"""


def diferencias_voz(engine: Engine, periodo: int) -> pd.DataFrame:
    """Ejecuta SQL_DIFERENCIAS con pd.read_sql(text(...), ..., params=...)."""
    raise NotImplementedError


if __name__ == "__main__":
    engine = crear_engine()
    cargar(engine, Path(sys.argv[1]))
    print(diferencias_voz(engine, int(sys.argv[2])))
