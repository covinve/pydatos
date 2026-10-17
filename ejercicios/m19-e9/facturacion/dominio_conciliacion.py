"""Dominio de la conciliación: comparar lo que se facturó con lo que se debió facturar.

Solo biblioteca estándar y facturacion.dominio. Define:

    FacturaEmitida  @dataclass(frozen=True): factura_id, linea, valor_voz, valor_internacional, valor_datos,
                    valor_sms, descuento, subtotal, iva, total (todos int salvo factura_id y linea)

    Hallazgo        @dataclass(frozen=True): factura_id, linea, tipo, emitido: int, correcto: int
                    tipo es uno de:
                      "consumo"        la suma de los cuatro valor_* emitidos difiere de la correcta
                                       (emitido y correcto son esas sumas)
                      "inconsistente"  en la factura emitida, total != subtotal + iva
                                       (emitido = total, correcto = subtotal + iva de la emitida)
                      "total"          el total emitido difiere del total correcto
                                       (emitido y correcto son los totales)

    revisar(emitida: FacturaEmitida, correcta: Factura) -> list[Hallazgo]
        Los hallazgos de una factura, en el orden consumo, inconsistente, total ([] si está bien).

    resumir(pares: list[tuple[FacturaEmitida, Factura]]) -> dict
        Con las claves de la sección "facturacion" de esperado.json:
        facturas, total_facturado, total_correcto, facturas_con_diferencia_consumo, facturas_inconsistentes,
        facturas_total_distinto, diferencia_total (emitido - correcto), diferencia_por_consumo (diferencia de
        TOTAL de las facturas con hallazgo "consumo"), iva_correcto.
"""
