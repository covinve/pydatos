"""Adaptadores CSV."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import astuple, fields
from datetime import date
from pathlib import Path

from facturacion.dominio import Cliente, Factura, Plan


class FuenteCSV:
    def __init__(self, carpeta):
        self.carpeta = Path(carpeta)

    def planes(self) -> dict[str, Plan]:
        with open(self.carpeta / "planes.csv", encoding="utf-8", newline="") as f:
            return {
                p["plan_id"]: Plan(p["plan_id"], int(p["cargo_fijo"]), int(p["minutos_incluidos"]),
                                   int(p["mb_incluidos"]), int(p["sms_incluidos"]), int(p["tarifa_minuto"]),
                                   int(p["tarifa_minuto_internacional"]), int(p["tarifa_mb"]), int(p["tarifa_sms"]))
                for p in csv.DictReader(f)
            }

    def clientes(self) -> list[Cliente]:
        with open(self.carpeta / "clientes.csv", encoding="latin-1", newline="") as f:
            return [Cliente(c["linea"], c["plan_id"], c["segmento"], date.fromisoformat(c["fecha_alta"]))
                    for c in csv.DictReader(f)]

    def cdrs(self) -> Iterator[dict]:
        with open(self.carpeta / "cdr.csv", encoding="utf-8", newline="") as f:
            yield from csv.DictReader(f, delimiter="|")


class SalidaCSV:
    def __init__(self, ruta):
        self.ruta = Path(ruta)

    def guardar(self, facturas: list[Factura]) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow([campo.name for campo in fields(Factura)])
            escritor.writerows(astuple(factura) for factura in facturas)
