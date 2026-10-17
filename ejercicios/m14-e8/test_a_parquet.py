"""Pruebas del ejercicio m14-e8."""

from pathlib import Path

import pandas as pd
import pytest

import a_parquet as ap

CSV = Path(__file__).parent / "cdr_muestra.csv"
ORIGINAL = pd.read_csv(CSV, sep="|", keep_default_na=False, dtype=str)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    carpeta = tmp_path_factory.mktemp("parquet") / "cdr"
    escritos = ap.convertir(CSV, carpeta, tamano_bloque=700)
    return carpeta, escritos


def test_cantidad(dataset):
    _, escritos = dataset
    assert escritos == len(ORIGINAL)


def test_particiones(dataset):
    carpeta, _ = dataset
    dias = sorted(p.name for p in carpeta.iterdir() if p.is_dir())
    assert "dia=2026-09-01" in dias and "dia=invalida" in dias
    assert len(dias) == 31, f"Se esperaban 30 días más 'invalida'; hay {len(dias)}"


def test_todo_el_dataset(dataset):
    carpeta, _ = dataset
    todo = pd.read_parquet(carpeta)
    assert len(todo) == len(ORIGINAL)
    assert pd.api.types.is_datetime64_any_dtype(todo["inicio"])
    assert int(todo["duracion_seg"].sum()) == int(ORIGINAL["duracion_seg"].astype(int).sum())


def test_leer_un_dia(dataset):
    carpeta, _ = dataset
    dia = ap.leer_dia(carpeta, "2026-09-15", columnas=["cdr_id", "tipo"])
    fechas = pd.to_datetime(ORIGINAL["fecha_inicio"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    esperado = int((fechas.dt.strftime("%Y-%m-%d") == "2026-09-15").sum())
    assert len(dia) == esperado
    assert set(dia.columns) <= {"cdr_id", "tipo", "dia"}

