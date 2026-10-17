"""Ejercicio m09-e9: un tarificador con reglas de descuento intercambiables.

Completa las clases según el enunciado del ejercicio en la página del curso.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Llamada:
    linea: str
    destino: str
    inicio: datetime
    segundos: int

    @property
    def minutos(self) -> int:
        return (self.segundos + 59) // 60


class ReglaDescuento(Protocol):
    """Contrato: cualquier objeto con este método es una regla de descuento."""

    def porcentaje(self, llamada: Llamada) -> int:
        """Devuelve el porcentaje de descuento (0 a 100) que aplica a la llamada."""
        ...


class SinDescuento:
    pass


class DescuentoNocturno:
    pass


class DescuentoFinDeSemana:
    pass


class Tarificador:
    pass
