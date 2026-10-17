"""Ejercicio m21-e9: una CLI configurable por capas (TOML < .env < entorno < argumentos).

Uso (cuando la termines):
    python ejercicios/m21-e9/telco_config.py mostrar --config config.toml
    python ejercicios/m21-e9/telco_config.py validar --config config.toml --env-file .env
    python ejercicios/m21-e9/telco_config.py ejecutar --config config.toml --umbral 1.5

Tu trabajo:

1. Config(BaseSettings) con prefijo "TELCO_", extra="forbid" e inmutable, y los campos:
       periodo: str = "202609"          (AAAAMM, mes 01-12)
       datos: Path = Path("datos")
       umbral_rechazo: float = 5.0      (0 a 100)
       hilos: int = 4                   (1 a 64)
       db_url: SecretStr | None = None
   con la precedencia: argumentos > entorno > .env > archivo TOML > valores por defecto
   (sobrescribe settings_customise_sources y usa TomlConfigSettingsSource).

2. crear_config(toml: Path | None, env_file: Path | None, **argumentos) -> Config
   Los argumentos con valor None no cuentan. Sin toml o sin env_file, esa capa no existe.

3. app = typer.Typer() con tres comandos, todos con las opciones --config (archivo TOML) y --env-file:
       mostrar    imprime una línea "campo = valor" por campo, en el orden de la clase,
                  con db_url como "***" si tiene valor. Con --json, imprime un JSON (también con "***").
       validar    si la configuración es válida imprime "Configuración válida" (código 0);
                  si no, una línea "✗ campo: mensaje" por cada error y termina con código 2.
       ejecutar   opciones --periodo y --umbral (sobrescriben); imprime
                  "Procesando {datos} periodo {periodo} con umbral {umbral_rechazo} y {hilos} hilos".
                  Si la configuración es inválida, igual que validar (código 2).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

app = None


if __name__ == "__main__":
    app()
