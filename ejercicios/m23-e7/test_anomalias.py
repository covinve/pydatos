"""Pruebas del ejercicio m23-e7: se plantan anomalías y el detector debe encontrarlas."""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import anomalias as a

DATOS = Path(__file__).parent / "datos_prueba"
CLIENTES = pd.read_csv(DATOS / "clientes.csv", encoding="latin-1", dtype={"linea": str})


def validos():
    cdr = pd.read_csv(DATOS / "cdr.csv", sep="|", dtype=str, keep_default_na=False)
    cdr = cdr[~cdr["cdr_id"].duplicated()]
    dur = pd.to_numeric(cdr["duracion_seg"])
    fecha = pd.to_datetime(cdr["fecha_inicio"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    ok = cdr["linea_origen"].isin(CLIENTES["linea"]) & cdr["tipo"].isin(["VOZ", "SMS", "DATOS"]) & (dur >= 0) & fecha.notna()
    return cdr[ok].assign(dur=dur[ok], hora=fecha[ok].dt.hour, mb=pd.to_numeric(cdr.loc[ok, "mb"]))


@pytest.fixture(scope="module")
def plantados(tmp_path_factory):
    """Copia los datos y agrega tres comportamientos anómalos a tres clientes residenciales."""
    carpeta = tmp_path_factory.mktemp("plantados")
    for archivo in ("cdr.csv", "clientes.csv"):
        shutil.copy(DATOS / archivo, carpeta / archivo)
    residenciales = CLIENTES.loc[CLIENTES["segmento"] == "RESIDENCIAL", "linea"].tolist()
    fraude, datos, sms = residenciales[1], residenciales[5], residenciales[9]
    filas, cdr_id = [], 90_000_000
    for i in range(80):            # llamadas internacionales largas de madrugada (SIM clonada)
        cdr_id += 1
        filas.append(f"{cdr_id}|{fraude}|0044207{i:07d}|VOZ|INTERNACIONAL|2026-09-{1 + i % 28:02d} 02:{i % 60:02d}:00|1800|0.000|CEL00001")
    for i in range(600):           # 1,8 TB de datos
        cdr_id += 1
        filas.append(f"{cdr_id}|{datos}||DATOS||2026-09-{1 + i % 28:02d} 13:00:00|600|3000.000|CEL00002")
    for i in range(600):           # envío masivo de SMS de madrugada
        cdr_id += 1
        filas.append(f"{cdr_id}|{sms}|3009990000|SMS|NACIONAL|2026-09-{1 + i % 28:02d} 03:00:00|0|0.000|CEL00003")
    with open(carpeta / "cdr.csv", "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(filas) + "\n")
    return carpeta, {fraude, datos, sms}


def test_caracteristicas():
    df = a.caracteristicas(DATOS)
    assert list(df.columns) == a.COLUMNAS
    assert df.index.name == "linea"
    assert list(df.index) == sorted(CLIENTES["linea"]), "Una fila por cada cliente, ordenadas"
    v = validos()
    voz = v[v["tipo"] == "VOZ"].assign(m=lambda d: (d["dur"] + 59) // 60)
    assert int(df["llamadas"].sum()) == len(voz)
    assert int(df["minutos"].sum()) == int(voz["m"].sum())
    assert int(df["sms"].sum()) == int((v["tipo"] == "SMS").sum())
    assert abs(df["mb"].sum() - v.loc[v["tipo"] == "DATOS", "mb"].sum()) < 0.1
    linea = voz["linea_origen"].value_counts().index[0]
    propia = voz[voz["linea_origen"] == linea]
    esperado_int = propia.loc[propia["destino"] == "INTERNACIONAL", "m"].sum() / propia["m"].sum()
    assert df.loc[linea, "pct_internacional"] == round(esperado_int, 4)
    assert df.loc[linea, "pct_nocturno"] == round((propia["hora"] < 6).mean(), 4)
    assert ((df["pct_internacional"] >= 0) & (df["pct_internacional"] <= 1)).all()


def test_puntaje_reproducible():
    df = a.caracteristicas(DATOS)
    p1, p2 = a.puntuar(df), a.puntuar(df)
    assert list(p1.index) == list(df.index)
    assert np.allclose(p1, p2), "Con la misma semilla, el mismo puntaje"


def test_encuentra_las_plantadas(plantados):
    carpeta, raras = plantados
    top = a.sospechosas(carpeta, n=6)
    assert list(top.columns) == a.COLUMNAS + ["puntaje"]
    assert list(top["puntaje"]) == sorted(top["puntaje"], reverse=True)
    encontradas = raras & set(top.index)
    assert encontradas == raras, f"Faltan en el top 6: {raras - encontradas}"
