"""Interfaz de línea de comandos (raíz de composición), con Typer.

app = typer.Typer(...) con dos comandos:

    telco ejecutar [--config archivo.toml] [--env-file .env] [--datos CARPETA] [--salidas CARPETA] [--periodo AAAAMM]
        1. Crea la configuración (config.crear_config). Si es inválida: una línea "✗ campo: mensaje" por error
           (en stderr) y código 2.
        2. Configura el logging del paquete: a stderr y a <salidas>/<periodo>/pipeline.log (sin duplicar manejadores).
        3. pipeline.ejecutar(config). Si faltan archivos (FileNotFoundError): mensaje y código 2.
        4. Imprime un resumen de una línea y dónde quedaron los resultados.
        5. Código 1 si no cuadra con esperado.json o hay alerta de rechazo; si no, 0.

    telco config [--config archivo.toml] [--env-file .env]
        Imprime "campo = valor" por cada campo de la configuración efectiva.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from telco_pipeline import pipeline
from telco_pipeline.config import crear_config

app = None


if __name__ == "__main__":
    app()
