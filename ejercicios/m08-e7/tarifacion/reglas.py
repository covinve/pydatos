from tarifacion.reportes import formatear_pesos

TARIFAS = {"LOCAL": 100, "NACIONAL": 120, "INTERNACIONAL": 950}


def valor_llamada(destino: str, segundos: int) -> int:
    return (segundos + 59) // 60 * TARIFAS[destino]


def describir_cobro(destino: str, segundos: int) -> str:
    return f"{destino.lower()} {segundos} s → {formatear_pesos(valor_llamada(destino, segundos))}"
