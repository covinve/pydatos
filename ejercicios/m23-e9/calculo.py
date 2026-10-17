"""Cálculo de la facturación correcta (ya está hecho y probado: es el del proyecto 2, con Pandas).

    facturas_correctas(carpeta) -> DataFrame con una fila por cliente:
        linea, plan_id, segmento, cargo_fijo, valor_voz, valor_internacional, valor_datos, valor_sms,
        descuento, subtotal, iva, total
    facturas_emitidas(carpeta) -> DataFrame de facturas.csv (la línea como texto)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FORMATO = "%Y-%m-%d %H:%M:%S"


def _redondear(x):
    return np.floor(np.asarray(x, dtype=float) + 0.5).astype("int64")


def _excedente(usado, incluido, tarifa):
    return np.where(incluido == -1, 0, np.maximum(0, usado - incluido) * tarifa).astype("int64")


def consumo_valido(carpeta: Path) -> pd.DataFrame:
    carpeta = Path(carpeta)
    cdr = pd.read_csv(carpeta / "cdr.csv", sep="|", dtype=str, keep_default_na=False)
    lineas = pd.read_csv(carpeta / "clientes.csv", encoding="latin-1", dtype=str)["linea"]
    duracion = pd.to_numeric(cdr["duracion_seg"])
    fecha = pd.to_datetime(cdr["fecha_inicio"], format=FORMATO, errors="coerce")
    ok = (~cdr["cdr_id"].duplicated() & cdr["linea_origen"].isin(lineas)
          & cdr["tipo"].isin(["VOZ", "SMS", "DATOS"]) & (duracion >= 0) & fecha.notna())
    v = cdr[ok].assign(minutos=(duracion[ok] + 59) // 60, mb=pd.to_numeric(cdr.loc[ok, "mb"]))
    voz = v["tipo"] == "VOZ"
    internacional = v["destino"] == "INTERNACIONAL"
    return pd.DataFrame({
        "min_nac": v["minutos"].where(voz & ~internacional, 0),
        "min_int": v["minutos"].where(voz & internacional, 0),
        "mb": v["mb"].where(v["tipo"] == "DATOS", 0.0),
        "sms": (v["tipo"] == "SMS").astype(int),
        "linea": v["linea_origen"],
    }).groupby("linea").sum()


def facturas_correctas(carpeta: Path) -> pd.DataFrame:
    carpeta = Path(carpeta)
    clientes = pd.read_csv(carpeta / "clientes.csv", encoding="latin-1", dtype={"linea": str})
    planes = pd.read_csv(carpeta / "planes.csv")
    c = clientes.merge(planes.drop(columns=["segmento", "nombre"]), on="plan_id")
    c = c.join(consumo_valido(carpeta), on="linea").fillna({"min_nac": 0, "min_int": 0, "mb": 0.0, "sms": 0})
    f = c[["linea", "plan_id", "segmento", "cargo_fijo"]].copy()
    f["valor_voz"] = _excedente(c["min_nac"], c["minutos_incluidos"], c["tarifa_minuto"])
    f["valor_internacional"] = (c["min_int"] * c["tarifa_minuto_internacional"]).astype("int64")
    f["valor_datos"] = _excedente(np.ceil(c["mb"].round(6)), c["mb_incluidos"], c["tarifa_mb"])
    f["valor_sms"] = _excedente(c["sms"], c["sms_incluidos"], c["tarifa_sms"])
    antiguo = (c["segmento"] == "EMPRESARIAL") & (c["fecha_alta"] < "2023-09-01")
    f["descuento"] = np.where(antiguo, _redondear(c["cargo_fijo"] * 0.10), 0)
    f["subtotal"] = (f["cargo_fijo"] + f["valor_voz"] + f["valor_internacional"] + f["valor_datos"]
                     + f["valor_sms"] - f["descuento"])
    f["iva"] = _redondear(f["subtotal"] * 0.19)
    f["total"] = f["subtotal"] + f["iva"]
    return f


def facturas_emitidas(carpeta: Path) -> pd.DataFrame:
    return pd.read_csv(Path(carpeta) / "facturas.csv", dtype={"linea": str, "periodo": str})
