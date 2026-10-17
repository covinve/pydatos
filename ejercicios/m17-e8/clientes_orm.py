"""Ejercicio m17-e8: clientes, planes e historial de cambios de plan con el ORM de SQLAlchemy.

Los modelos ya están definidos: tu trabajo son las cuatro funciones del final.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from sqlalchemy import Date, ForeignKey, String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Plan(Base):
    __tablename__ = "planes"

    plan_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str]
    segmento: Mapped[str]
    cargo_fijo: Mapped[int]

    clientes: Mapped[list[Cliente]] = relationship(back_populates="plan")


class Cliente(Base):
    __tablename__ = "clientes"

    linea: Mapped[str] = mapped_column(String(10), primary_key=True)
    cliente_id: Mapped[str]
    nombre: Mapped[str]
    segmento: Mapped[str]
    fecha_alta: Mapped[date] = mapped_column(Date)
    plan_id: Mapped[str] = mapped_column(ForeignKey("planes.plan_id"))

    plan: Mapped[Plan] = relationship(back_populates="clientes")
    historial: Mapped[list[HistorialPlan]] = relationship(back_populates="cliente", order_by="HistorialPlan.desde")


class HistorialPlan(Base):
    """Qué plan tuvo cada línea y desde/hasta cuándo (hasta = None: vigente)."""

    __tablename__ = "historial_planes"

    id: Mapped[int] = mapped_column(primary_key=True)
    linea: Mapped[str] = mapped_column(ForeignKey("clientes.linea"))
    plan_id: Mapped[str] = mapped_column(ForeignKey("planes.plan_id"))
    desde: Mapped[date] = mapped_column(Date)
    hasta: Mapped[date | None] = mapped_column(Date)

    cliente: Mapped[Cliente] = relationship(back_populates="historial")


# ---------------------------------------------------------------------------
# Tu trabajo
# ---------------------------------------------------------------------------

def cargar_catalogos(sesion: Session, carpeta: Path) -> tuple[int, int]:
    """Crea los Plan de planes.csv y los Cliente de clientes.csv (latin-1), y para cada cliente
    un HistorialPlan con su plan actual desde su fecha_alta (hasta = None). Confirma y devuelve
    (cantidad_de_planes, cantidad_de_clientes)."""
    raise NotImplementedError


def cambiar_plan(sesion: Session, linea: str, plan_id: str, fecha: date) -> None:
    """Cambia el plan de la línea a partir de `fecha`:
    - LookupError si la línea o el plan no existen;
    - ValueError si ya tiene ese plan o si `fecha` no es posterior al inicio del plan vigente;
    - cierra el historial vigente (hasta = fecha), crea uno nuevo (desde = fecha), actualiza el cliente y confirma.
    """
    raise NotImplementedError


def plan_vigente(sesion: Session, linea: str, dia: date) -> str | None:
    """plan_id que tenía la línea ese día (desde <= dia < hasta, o hasta nulo); None si aún no era cliente."""
    raise NotImplementedError


def resumen_por_segmento(sesion: Session) -> list[tuple[str, int, int]]:
    """[(segmento, clientes, suma_de_cargo_fijo_de_sus_planes), ...] ordenado por segmento,
    con UNA consulta select(...).join(...).group_by(...)."""
    raise NotImplementedError
