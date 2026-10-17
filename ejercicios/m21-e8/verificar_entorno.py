"""Ejercicio m21-e8: ¿mi entorno es exactamente el del archivo de bloqueo?

Uso:
    python ejercicios/m21-e8/verificar_entorno.py requirements.lock
    python ejercicios/m21-e8/verificar_entorno.py requirements.lock --estricto

Funciones:

    normalizar(nombre) -> str
        Minúsculas, y cualquier grupo de "-", "_" o "." convertido en un solo "-".

    leer_bloqueo(texto) -> dict[str, str]
        {nombre_normalizado: version} del contenido de un archivo de bloqueo (formato de pip-compile):
          - ignora líneas vacías, comentarios ("# via pandas") y opciones ("--index-url ...");
          - cada requisito es "nombre==version", quizás con extras ("uvicorn[standard]==0.30.6"),
            con un marcador después de ";" ("tzdata==2024.2 ; sys_platform == 'win32'") o
            seguido de " \\" y líneas "--hash=sha256:..." que también se ignoran;
          - una línea de requisito que NO usa "==" es un error: ValueError con esa línea.

    instaladas() -> dict[str, str]
        {nombre_normalizado: version} de los paquetes instalados (importlib.metadata.distributions()).

    comparar(bloqueo, instaladas) -> dict
        {"faltan": [nombres en el bloqueo no instalados],
         "distintas": [(nombre, version_bloqueo, version_instalada)],
         "sobran": [instalados que no están en el bloqueo, sin contar pip, setuptools ni wheel]}
        Todas las listas ordenadas por nombre.

    main(argv=None) -> int
        Lee el bloqueo, compara con instaladas() e imprime un informe:
            "✅ Entorno igual al bloqueo (N paquetes)"         si no hay faltantes ni distintas
            "❌ Falta: nombre==version"                      una línea por cada faltante
            "❌ Distinta: nombre (bloqueo X, instalada Y)"    una por cada distinta
            "⚠️  Sobra: nombre==version"                      una por cada sobrante
        Código de salida: 1 si hay faltantes o distintas (o sobrantes con --estricto); si no, 0.
        Si el archivo no existe: mensaje en stderr y código 2.
"""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path
