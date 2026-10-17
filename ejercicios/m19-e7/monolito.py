"""El script de facturación "de toda la vida": funciona, pero todo está mezclado.

Uso:
    python ejercicios/m19-e7/monolito.py ejercicios/m19-e7/datos_prueba salidas/facturas.csv

NO lo modifiques: es la referencia. Tu trabajo es reorganizarlo en el paquete facturacion/.
"""

import csv
import math
import sys
from datetime import datetime
from pathlib import Path


def main(carpeta, ruta_salida):
    carpeta = Path(carpeta)
    planes = {}
    with open(carpeta / "planes.csv", encoding="utf-8", newline="") as f:
        for p in csv.DictReader(f):
            planes[p["plan_id"]] = p
    clientes = []
    with open(carpeta / "clientes.csv", encoding="latin-1", newline="") as f:
        for c in csv.DictReader(f):
            clientes.append(c)
    lineas = {c["linea"] for c in clientes}

    consumo = {}
    vistos = set()
    with open(carpeta / "cdr.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="|"):
            if r["cdr_id"] in vistos:
                continue
            vistos.add(r["cdr_id"])
            if not r["linea_origen"] or r["linea_origen"] not in lineas:
                continue
            if r["tipo"] not in ("VOZ", "SMS", "DATOS") or int(r["duracion_seg"]) < 0:
                continue
            try:
                datetime.strptime(r["fecha_inicio"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            c = consumo.setdefault(r["linea_origen"], {"nac": 0, "int": 0, "mb": 0.0, "sms": 0})
            if r["tipo"] == "VOZ":
                minutos = (int(r["duracion_seg"]) + 59) // 60
                if r["destino"] == "INTERNACIONAL":
                    c["int"] += minutos
                else:
                    c["nac"] += minutos
            elif r["tipo"] == "DATOS":
                c["mb"] += float(r["mb"])
            else:
                c["sms"] += 1

    filas = []
    total_general = 0
    for cli in clientes:
        p = planes[cli["plan_id"]]
        c = consumo.get(cli["linea"], {"nac": 0, "int": 0, "mb": 0.0, "sms": 0})
        cargo = int(p["cargo_fijo"])
        if int(p["minutos_incluidos"]) == -1:
            voz = 0
        else:
            voz = max(0, c["nac"] - int(p["minutos_incluidos"])) * int(p["tarifa_minuto"])
        inter = c["int"] * int(p["tarifa_minuto_internacional"])
        if int(p["mb_incluidos"]) == -1:
            datos = 0
        else:
            datos = max(0, math.ceil(round(c["mb"], 6)) - int(p["mb_incluidos"])) * int(p["tarifa_mb"])
        if int(p["sms_incluidos"]) == -1:
            sms = 0
        else:
            sms = max(0, c["sms"] - int(p["sms_incluidos"])) * int(p["tarifa_sms"])
        if cli["segmento"] == "EMPRESARIAL" and cli["fecha_alta"] < "2023-09-01":
            descuento = int(cargo * 0.10 + 0.5)
        else:
            descuento = 0
        subtotal = cargo + voz + inter + datos + sms - descuento
        iva = int(subtotal * 0.19 + 0.5)
        total = subtotal + iva
        total_general += total
        filas.append([cli["linea"], cli["plan_id"], cargo, voz, inter, datos, sms, descuento, subtotal, iva, total])

    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["linea", "plan_id", "cargo_fijo", "valor_voz", "valor_internacional", "valor_datos",
                    "valor_sms", "descuento", "subtotal", "iva", "total"])
        w.writerows(filas)
    total_texto = f"{total_general:,}".replace(",", ".")
    print(f"{len(filas)} facturas, total ${total_texto}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
