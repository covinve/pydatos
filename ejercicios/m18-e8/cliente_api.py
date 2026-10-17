"""Ejercicio m18-e8: un cliente de verdad para la API de tarifas y consumos.

Las pruebas levantan un servidor HTTP local que se comporta como la API real (incluidos sus fallos).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Iterator

import requests


class ClienteAPI:
    """Cliente de la API de facturación.

    - token: si es None, se lee de la variable de entorno TELCO_API_TOKEN; si no hay, ValueError.
    - Todas las peticiones usan una requests.Session con la cabecera "Authorization: Bearer <token>"
      y timeout=self.timeout.
    - Reintentos (hasta `intentos` llamadas en total) ante requests.ConnectionError, requests.Timeout,
      estado 429 o 5xx, esperando con self.dormir(segundos): Retry-After si el 429 lo trae;
      si no, base * 2**n (n = número de reintento, empezando en 0). Si se agotan: se relanza la
      excepción o se llama raise_for_status() sobre la última respuesta.
    - 401 o 403 → PermissionError inmediatamente (sin reintentar).
    """

    def __init__(self, url_base: str, token: str | None = None, timeout: float = 10, intentos: int = 4,
                 base: float = 1.0, dormir: Callable[[float], None] = time.sleep):
        raise NotImplementedError

    def tarifa(self, plan_id: str) -> dict:
        """GET {url_base}/tarifas/{plan_id} → el JSON. 404 → LookupError."""
        raise NotImplementedError

    def consumos(self, periodo: str, tamano: int = 20) -> Iterator[dict]:
        """GET {url_base}/consumos?periodo=...&pagina=N&tamano=... desde la página 1.
        La respuesta es {"datos": [...], "pagina": N, "total_paginas": T}.
        Generador: entrega los registros uno a uno hasta la última página."""
        raise NotImplementedError

    def registrar_ajuste(self, factura_id: str, valor: int, motivo: str) -> dict:
        """POST {url_base}/ajustes con JSON {"factura_id", "valor", "motivo"} y la cabecera
        "Idempotency-Key: <factura_id>:<valor>:<motivo>" (así reintentar nunca duplica). Devuelve el JSON."""
        raise NotImplementedError
