"""Puertos: lo que el servicio necesita del exterior, como Protocol."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from facturacion.dominio import Cliente, Factura, Plan


class FuenteDatos(Protocol):
    def planes(self) -> dict[str, Plan]: ...
    def clientes(self) -> list[Cliente]: ...
    def cdrs(self) -> Iterable[dict]: ...


class SalidaFacturas(Protocol):
    def guardar(self, facturas: list[Factura]) -> None: ...
