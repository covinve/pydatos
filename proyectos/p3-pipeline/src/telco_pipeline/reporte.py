"""Escritura de resultados: JSON, CSV para Excel, gráfico e informe Markdown."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def pesos(valor: int) -> str:
    """$1.234.567 (negativos: -$5.000)."""
    raise NotImplementedError


def escribir(salida: Path, resultado: dict, diferencias: pd.DataFrame, anomalias: pd.DataFrame) -> list[Path]:
    """Escribe en `salida` y devuelve las rutas de:

    resumen.json      `resultado` completo (el diccionario que arma pipeline.ejecutar)
    diferencias.csv   separador ";" y codificación utf-8-sig (para abrir con doble clic en Excel)
    anomalias.csv     igual, con la línea como primera columna
    rechazos.png      barras con los CDR rechazados por motivo
    informe.md        con las secciones:
                        "# Pipeline de facturación · periodo AAAAMM"
                        "## Resumen"               tabla de indicadores (montos con pesos())
                        "## Rechazos"              con "![Rechazos por motivo](rechazos.png)"
                        "## Mayores diferencias"   las 10 primeras diferencias
                        "## Líneas sospechosas"    las 10 primeras anomalías
                        "## Tiempos"               una fila por etapa
    """
    raise NotImplementedError
