"""Proceso nocturno de conteo de archivos de CDR. NO lo modifiques: escribe sus pruebas."""

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("proceso")


def carpeta_entrada() -> Path:
    """La carpeta viene de la variable de entorno CARPETA_CDR; si no existe, se usa 'entrada'."""
    return Path(os.environ.get("CARPETA_CDR", "entrada"))


def contar_registros(ruta: Path) -> int:
    with open(ruta, encoding="utf-8") as archivo:
        return max(0, sum(1 for _ in archivo) - 1)


def main(argumentos: list[str] | None = None) -> int:
    """Cuenta los registros de cada cdr_*.csv de la carpeta de entrada.

    - Imprime una línea por archivo ("cdr_01.csv: 3 registros") y al final "Total: N registros".
    - Registra un WARNING por cada archivo vacío (solo encabezado).
    - Con la opción --minimo N, si el total es menor que N registra un ERROR y devuelve 1.
    - Si la carpeta no existe, registra un ERROR y devuelve 2.
    - Si todo sale bien devuelve 0.
    """
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    minimo = int(argumentos[argumentos.index("--minimo") + 1]) if "--minimo" in argumentos else 0
    carpeta = carpeta_entrada()
    if not carpeta.is_dir():
        log.error("No existe la carpeta %s", carpeta)
        return 2
    total = 0
    for ruta in sorted(carpeta.glob("cdr_*.csv")):
        cantidad = contar_registros(ruta)
        if cantidad == 0:
            log.warning("Archivo vacío: %s", ruta.name)
        print(f"{ruta.name}: {cantidad} registros")
        total += cantidad
    print(f"Total: {total} registros")
    if total < minimo:
        log.error("Se esperaban al menos %d registros y llegaron %d", minimo, total)
        return 1
    return 0
