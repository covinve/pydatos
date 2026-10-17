from decimal import ROUND_HALF_UP, Decimal


def formatear_pesos(valor: float | int | Decimal) -> str:
    """Formatea un valor en pesos colombianos: 48719.5 -> "$48.720"."""
    pesos = Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    signo = "-" if pesos < 0 else ""
    return f"{signo}${abs(pesos):,}".replace(",", ".")
