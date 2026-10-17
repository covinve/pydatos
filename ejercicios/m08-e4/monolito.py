"""Reporte de consumo de voz: TODO en un solo archivo.

Funciona, pero es difícil de probar y de reutilizar. Tu tarea es dividirlo en el
paquete `facturador/` (ver el enunciado del ejercicio m08-e4). No modifiques este archivo:
las pruebas lo usan para comparar resultados.

Uso:
    python ejercicios/m08-e4/monolito.py ejercicios/m08-e4/llamadas.csv
"""

import csv
import sys

TIPOS = {"VOZ", "SMS", "DATOS"}

ruta = sys.argv[1] if len(sys.argv) > 1 else "llamadas.csv"
minutos_por_linea = {}
validos = 0
invalidos = 0
with open(ruta, encoding="utf-8", newline="") as archivo:
    for fila in csv.DictReader(archivo, delimiter="|"):
        duracion = int(fila["duracion_seg"])
        if fila["tipo"] not in TIPOS or duracion < 0:
            invalidos += 1
            continue
        validos += 1
        if fila["tipo"] == "VOZ":
            minutos = (duracion + 59) // 60
            linea = fila["linea_origen"]
            minutos_por_linea[linea] = minutos_por_linea.get(linea, 0) + minutos

print(f"Registros válidos: {validos} · inválidos: {invalidos}")
for linea, minutos in sorted(minutos_por_linea.items(), key=lambda par: (-par[1], par[0])):
    print(f"  {linea}: {minutos} min")
print(f"Total: {sum(minutos_por_linea.values())} min")
