"""Reporte rápido del consumo de una línea."""
import os
import sys

GIGA = 1024


def MegasAGigas(Megas):
    Resultado = round(Megas / GIGA, 2)
    return Resultado


def ResumenConsumo(linea, minutos, megas, plan=None):
    if plan == None:
        plan = "SIN PLAN"
    total_cdr = minutos + megas
    gigas = MegasAGigas(megas)
    return f"Línea {linea} ({plan}): {minutos} min de voz y {gigas} GB de datos"


if __name__ == "__main__":
    print(ResumenConsumo("3001234567", 342, 20480, "HOG30"))
    print(ResumenConsumo("3109876543", 15, 512))
