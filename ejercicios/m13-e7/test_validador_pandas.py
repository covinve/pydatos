"""Pruebas del ejercicio m13-e7."""

import json
from pathlib import Path

import pandas as pd
import pytest

import validador_pandas as v

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
CLAVES = ["registros_totales", "registros_validos", "errores", "validos_por_tipo", "minutos_nacionales",
          "minutos_internacionales", "mb_totales", "sms_totales", "lineas_con_consumo"]


@pytest.fixture(scope="module")
def resultado(tmp_path_factory):
    salida = tmp_path_factory.mktemp("salida")
    return v.validar(DATOS, salida), salida


def test_lectura_con_tipos():
    cdr, clientes = v.leer(DATOS)
    assert pd.api.types.is_string_dtype(cdr["linea_origen"])
    assert pd.api.types.is_string_dtype(clientes["linea"])


@pytest.mark.parametrize("clave", CLAVES)
def test_resumen(resultado, clave):
    resumen, _ = resultado
    if clave == "mb_totales":
        assert abs(resumen[clave] - ESPERADO[clave]) < 0.01
    else:
        assert resumen[clave] == ESPERADO[clave]


def test_archivos(resultado):
    resumen, salida = resultado
    rechazados = pd.read_csv(salida / "rechazados.csv", sep="|", dtype=str, keep_default_na=False)
    assert len(rechazados) == sum(ESPERADO["errores"].values())
    assert rechazados.columns[-1] == "motivo"
    assert json.loads((salida / "resumen.json").read_text(encoding="utf-8"))["registros_totales"] == resumen["registros_totales"]


def test_vectorizado():
    texto = (Path(__file__).parent / "validador_pandas.py").read_text(encoding="utf-8")
    assert ".apply(" not in texto and "iterrows" not in texto and "itertuples" not in texto
