"""Ejercicio m23-e9: el informe mensual de aseguramiento de ingresos.

Uso:
    python ejercicios/m23-e9/informe.py datos/100MB salidas/informe_202609

generar_informe(carpeta, salida) -> dict
    Usa calculo.facturas_correctas y calculo.facturas_emitidas (ya hechos), une por línea y escribe en `salida`:

    resumen.json      {"periodo", "facturas", "total_facturado", "total_correcto", "diferencia_total",
                       "facturas_con_diferencia", "perdida", "cobro_de_mas"}
                      diferencia = total emitido − total correcto; "perdida" = suma de |diferencias negativas|
                      (se cobró de menos); "cobro_de_mas" = suma de diferencias positivas; todos enteros.
                      "periodo" es el de las facturas emitidas (texto AAAAMM).
    diferencias.csv   factura_id, linea, plan_id, facturado, correcto, diferencia: solo las facturas con
                      diferencia distinta de 0, ordenadas por |diferencia| de mayor a menor (utf-8).
    diferencias.png   gráfico de barras (matplotlib, sin abrir ventanas) con la diferencia total por plan.
    informe.md        Markdown con:
                        "# Informe de aseguramiento de ingresos · periodo AAAAMM"
                        "## Resumen"   una tabla | Indicador | Valor | con los indicadores del resumen,
                                       los montos con formato $1.234.567
                        "## Mayores diferencias"  tabla con las (hasta) 10 primeras filas de diferencias.csv
                        "![Diferencias por plan](diferencias.png)"
    Devuelve el resumen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")                      # sin ventanas: funciona en tareas programadas y en Docker
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import calculo  # noqa: E402


if __name__ == "__main__":
    print(generar_informe(Path(sys.argv[1]), Path(sys.argv[2])))
