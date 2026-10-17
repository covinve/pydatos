"""Caso de uso: facturar el periodo."""

from __future__ import annotations

from facturacion.dominio import Consumo, calcular_factura, consumo_por_linea
from facturacion.puertos import FuenteDatos, SalidaFacturas


def facturar(fuente: FuenteDatos, salida: SalidaFacturas) -> dict:
    planes = fuente.planes()
    clientes = fuente.clientes()
    consumos = consumo_por_linea(fuente.cdrs(), {c.linea for c in clientes})
    facturas = [calcular_factura(c, planes[c.plan_id], consumos.get(c.linea, Consumo())) for c in clientes]
    salida.guardar(facturas)
    return {"facturas": len(facturas), "total": sum(f.total for f in facturas)}
