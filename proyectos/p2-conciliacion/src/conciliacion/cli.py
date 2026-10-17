"""Punto de entrada: conciliar --datos CARPETA --salida CARPETA"""

from __future__ import annotations


def main(argumentos: list[str] | None = None) -> int:
    """Lee los datos, valida, calcula, concilia, genera el reporte y muestra un resumen.
    Configura aquí el logging (consola y salida/conciliacion.log).
    Si junto a los datos existe esperado.json, compara el resumen y lo informa.
    Devuelve 0 si todo salió bien, 1 si el resumen no cuadra con esperado.json, 2 si faltan archivos."""
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
