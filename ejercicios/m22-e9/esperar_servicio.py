"""Ejercicio m22-e9: esperar a que un servicio (PostgreSQL, una API) acepte conexiones y luego ejecutar un comando.

Uso:
    python esperar_servicio.py bd:5432 --timeout 60 -- python -m app.cargar

Funciones:

    destino(texto) -> tuple[str, int]
        "bd:5432" → ("bd", 5432). Sin ":" o con un puerto que no es un número entre 1 y 65535: ValueError.

    esperar(host, puerto, timeout=30.0, intervalo=0.5, reloj=time.monotonic, dormir=time.sleep) -> float
        Intenta socket.create_connection((host, puerto), timeout=intervalo) hasta que funcione y devuelve los
        segundos que esperó (según `reloj`). Si falla (OSError), duerme `intervalo` y reintenta.
        Si ya pasaron `timeout` segundos sin éxito: TimeoutError con "host:puerto" en el mensaje.

    main(argv=None) -> int
        Argumentos: destino, --timeout (float, 30 por defecto) y, después de "--", el comando a ejecutar.
        Espera el servicio; si no responde a tiempo, escribe el error en stderr y devuelve 1.
        Si responde: imprime "bd:5432 disponible en X.X s", ejecuta el comando (si hay) con subprocess.run
        y devuelve SU código de salida (0 si no había comando).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
