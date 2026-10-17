"""Dominio: las reglas de facturación. Sin archivos, sin prints, sin csv ni pandas.

Define (todas con @dataclass(frozen=True)):

    Plan(plan_id: str, cargo_fijo: int, minutos_incluidos: int, mb_incluidos: int, sms_incluidos: int,
         tarifa_minuto: int, tarifa_minuto_internacional: int, tarifa_mb: int, tarifa_sms: int)
    Cliente(linea: str, plan_id: str, segmento: str, fecha_alta: date)
    Consumo(minutos_nacionales: int = 0, minutos_internacionales: int = 0, mb: float = 0.0, sms: int = 0)
    Factura(linea, plan_id, cargo_fijo, valor_voz, valor_internacional, valor_datos, valor_sms,
            descuento, subtotal, iva, total)            # todos int salvo linea y plan_id

Y las funciones:

    minutos_facturables(segundos: int) -> int
    cdr_valido(cdr: dict, lineas: set[str], vistos: set[str]) -> bool
        Las seis reglas del curso. `vistos` acumula los cdr_id ya revisados (para los duplicados).
    consumo_por_linea(cdrs: Iterable[dict], lineas: set[str]) -> dict[str, Consumo]
        Solo los CDR válidos; una entrada por línea con consumo.
    calcular_factura(cliente: Cliente, plan: Plan, consumo: Consumo) -> Factura
        Exactamente las reglas de monolito.py.
"""
