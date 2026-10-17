"""Lector de archivos de CDR (separados por |). NO lo modifiques: escribe sus pruebas."""

from collections import Counter
from pathlib import Path


def resumir(ruta: Path) -> dict:
    """Resume un archivo de CDR con encabezado.

    Devuelve:
      registros    cantidad de registros (sin el encabezado)
      por_tipo     {tipo: cantidad}, ordenado por tipo
      minutos_voz  minutos facturables de los VOZ con duración >= 0
      lineas       cantidad de líneas de origen distintas y no vacías
    """
    registros = 0
    por_tipo = Counter()
    minutos_voz = 0
    lineas = set()
    with open(ruta, encoding="utf-8") as archivo:
        encabezado = next(archivo).rstrip("\n").split("|")
        posicion = {nombre: i for i, nombre in enumerate(encabezado)}
        for linea in archivo:
            campos = linea.rstrip("\n").split("|")
            registros += 1
            tipo = campos[posicion["tipo"]]
            por_tipo[tipo] += 1
            if campos[posicion["linea_origen"]]:
                lineas.add(campos[posicion["linea_origen"]])
            duracion = int(campos[posicion["duracion_seg"]])
            if tipo == "VOZ" and duracion >= 0:
                minutos_voz += (duracion + 59) // 60
    return {
        "registros": registros,
        "por_tipo": dict(sorted(por_tipo.items())),
        "minutos_voz": minutos_voz,
        "lineas": len(lineas),
    }
