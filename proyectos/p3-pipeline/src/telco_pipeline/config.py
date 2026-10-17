"""Configuración del pipeline: valores por defecto < config.toml < .env < entorno (TELCO_*) < argumentos.

Lo construiste en el módulo 21 (ejercicio 9). Define:

class Config(BaseSettings)
    Prefijo de entorno "TELCO_", extra="forbid" (una clave desconocida es error) e inmutable (frozen=True).

    Campo            Por defecto            Reglas
    datos            Path("datos/10MB")
    salidas          Path("salidas")
    periodo          "202609"               AAAAMM con mes 01-12
    memoria_duckdb   "4GB"                  número + MB o GB; se guarda en mayúsculas ("8gb" → "8GB")
    hilos            4                      1 a 64
    umbral_rechazo   5.0                    0 a 100 (porcentaje de CDR rechazados que dispara la alerta)
    top_anomalias    20                     1 a 1000

    Precedencia: settings_customise_sources con (init, entorno, .env, TomlConfigSettingsSource).

def crear_config(toml: Path | None = None, env_file: Path | None = None, **argumentos) -> Config
    Sin toml o sin env_file, esa capa no existe. Los argumentos con valor None no cuentan.
"""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource


class Config:
    """Reemplázala por la clase de pydantic-settings descrita arriba."""


def crear_config(toml: Path | None = None, env_file: Path | None = None, **argumentos: object) -> Config:
    raise NotImplementedError
