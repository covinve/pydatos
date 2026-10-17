"""Ejercicio m21-e7: la configuración del pipeline, validada con pydantic-settings.

Define ConfigPipeline(BaseSettings) con:
    model_config: prefijo de entorno "TELCO_", archivo .env (utf-8), inmutable (frozen=True)
                  y extra="ignore" (otras variables del .env no molestan).

    Campo            Tipo / por defecto                   Reglas
    datos            Path (obligatorio)                   debe ser una carpeta que exista
    salidas          Path = Path("salidas")
    periodo          str (obligatorio)                    formato AAAAMM con mes 01-12
    umbral_rechazo   float = 5.0                          entre 0 y 100
    memoria_duckdb   str = "4GB"                          número + MB o GB (sin distinguir mayúsculas);
                                                          se guarda en mayúsculas: "8gb" → "8GB"
    hilos            int = 4                              entre 1 y 64
    correos_alerta   list[str] = []                       cada uno debe contener "@"
    db_url           SecretStr | None = None

    resumen() -> dict   todos los campos como texto (str(valor)) para mostrarlos; db_url como "***" si
                        tiene valor (o "" si es None) y correos_alerta unidos con ", ".

Y la función:
    cargar(env_file=".env", **sobrescritos) -> ConfigPipeline
        Crea la configuración leyendo `env_file` (o ninguno si es None). Los sobrescritos con valor None se ignoran.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
