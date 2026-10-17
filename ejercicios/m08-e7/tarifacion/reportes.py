from tarifacion.reglas import valor_llamada


def formatear_pesos(valor: int) -> str:
    return "$" + f"{valor:,}".replace(",", ".")


def reporte_linea(linea: str, llamadas: list[tuple[str, int]]) -> str:
    total = sum(valor_llamada(destino, segundos) for destino, segundos in llamadas)
    return f"{linea}: {len(llamadas)} llamadas · {formatear_pesos(total)}"
