"""Raíz de composición.

Uso:
    python -m facturacion.cli datos_prueba salidas/facturas.csv     (desde ejercicios/m19-e7)
"""

from __future__ import annotations

import sys

from facturacion.adaptadores_csv import FuenteCSV, SalidaCSV
from facturacion.servicios import facturar


def main(argv: list[str] | None = None) -> int:
    carpeta, ruta_salida = argv if argv is not None else sys.argv[1:3]
    resumen = facturar(FuenteCSV(carpeta), SalidaCSV(ruta_salida))
    total = f"{resumen['total']:,}".replace(",", ".")
    print(f"{resumen['facturas']} facturas, total ${total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
