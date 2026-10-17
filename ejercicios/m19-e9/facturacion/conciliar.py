"""Caso de uso: conciliar el periodo.

Solo biblioteca estándar y los módulos facturacion.dominio, facturacion.dominio_conciliacion y facturacion.puertos.

    FacturasEmitidas (Protocol):     todas() -> list[FacturaEmitida]
    SalidaConciliacion (Protocol):   publicar(resumen: dict, hallazgos: list[Hallazgo]) -> None

    conciliar(fuente: FuenteDatos, emitidas: FacturasEmitidas, salida: SalidaConciliacion) -> dict
        1. Calcula la factura correcta de cada cliente de `fuente` (con el dominio de facturación).
        2. Empareja cada factura emitida con la correcta de su línea (una emitida sin cliente → KeyError).
        3. Publica el resumen y TODOS los hallazgos (en el orden de las facturas emitidas) y devuelve el resumen.
"""
