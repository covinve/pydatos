"""Salidas para personas: archivos CSV, gráficos y el reporte en Markdown."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def generar(resumen: dict, diagnostico: pd.DataFrame, carpeta: Path) -> Path:
    """Escribe en `carpeta`:
      - diferencias.csv: el diagnóstico (separado por ;, UTF-8 con BOM para abrir en Excel)
      - diferencias_por_motivo.png y top_diferencias.png
      - reporte.md: título, indicadores del resumen, los dos gráficos y la tabla de las 10 mayores diferencias
    Devuelve la ruta de reporte.md."""
    raise NotImplementedError
