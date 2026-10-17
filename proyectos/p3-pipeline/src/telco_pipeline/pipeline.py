"""Orquestación: une las etapas, mide sus tiempos y registra lo que pasa (logger "telco_pipeline")."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from telco_pipeline import anomalias, conciliacion, consumo, facturacion, lectura, reporte, validacion
from telco_pipeline.config import Config

log = logging.getLogger("telco_pipeline")


def comparar_con_esperado(resultado: dict, esperado: dict) -> bool:
    """True si la validación coincide con esperado["cdr"] (registros, errores, minutos, sms; mb con tolerancia 0.01)
    y la conciliación con esperado["facturacion"] (todas sus claves)."""
    raise NotImplementedError


def ejecutar(config: Config) -> dict:
    """Ejecuta el pipeline con los resultados en config.salidas / config.periodo:

      1. verificar los archivos de config.datos (FileNotFoundError si falta alguno)
      2. "validacion"     validacion.validar(...)  → validos.parquet y rechazos.parquet
      3. "facturacion"    lectura + consumo.consumo_por_linea + facturacion.facturas_correctas
      4. "conciliacion"   conciliacion.conciliar
      5. "anomalias"      anomalias.top(consumo.perfil_lineas(...), config.top_anomalias)
      6. comparar con datos/esperado.json, si existe
      7. "reporte"        reporte.escribir(...)

    Mide el tiempo de cada etapa (en segundos, 3 decimales) y registra con logging el inicio y fin de cada una,
    los conteos principales y una advertencia si el rechazo supera config.umbral_rechazo. Devuelve:

    {"periodo", "validacion": resumen de validar, "facturacion": resumen de conciliar,
     "anomalias": cantidad de líneas en el top, "porcentaje_rechazo" (3 decimales),
     "alerta_rechazo": bool, "cuadra": True/False/None (None si no hay esperado.json), "tiempos": {etapa: s}}
    """
    raise NotImplementedError
