"""Tarificador de llamadas heredado de otro equipo.

Funciona sin errores... pero los valores no cuadran. Tiene TRES errores escondidos.
Encuéntralos con el depurador de VS Code (F5) y corrígelos.

Uso:
    python ejercicios/m07-e5/tarificador.py
"""

from pathlib import Path

TARIFAS = {"LOCAL": 100, "NACIONAL": 120, "INTERNACIONAL": 950}


def leer_registro(linea):
    campos = linea.strip().split("|")
    return {
        "linea": campos[1],
        "tipo": campos[3],
        "destino": campos[4],
        "duracion": int(campos[6]),
    }


def minutos(segundos):
    """Minutos facturables: se cobra cada minuto iniciado."""
    return segundos // 60 + 1


def tarifa(destino, tarifas):
    return tarifas.get(destino.title(), 0)


def valor_por_linea(lineas_archivo, tarifas, acumulado={}):
    """Suma el valor de las llamadas de voz de cada línea. Recibe las líneas del archivo con encabezado."""
    for texto in lineas_archivo[1:]:
        registro = leer_registro(texto)
        if registro["tipo"] == "VOZ":
            valor = minutos(registro["duracion"]) * tarifa(registro["destino"], tarifas)
            acumulado[registro["linea"]] = acumulado.get(registro["linea"], 0) + valor
    return acumulado


if __name__ == "__main__":
    ruta = Path(__file__).parent / "llamadas.csv"
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    print(valor_por_linea(lineas, TARIFAS))
