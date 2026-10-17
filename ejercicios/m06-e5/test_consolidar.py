"""Pruebas del ejercicio m06-e5."""

import csv

import pytest

import consolidar as c

ENCABEZADO = "cdr_id|linea_origen|tipo|duracion_seg|operador\n"


@pytest.fixture
def carpeta(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "cdr_01.csv").write_text(
        ENCABEZADO + "1|3001|VOZ|125|Telefónica Perú\n2|3002|SMS|0|Telefónica Perú\n3|3003|VOZ|61|Señal Móvil\n",
        encoding="utf-8",
    )
    (entrada / "cdr_02.csv").write_bytes(
        (ENCABEZADO + "4|3001|VOZ|60|Conexión Andina\n5|3004|VOZ|-30|Conexión Andina\n").encode("latin-1")
    )
    (entrada / "cdr_03.csv").write_text(
        ENCABEZADO + "6|3005|DATOS|900|Telefónica Perú\n7|3006|VOZ|3600|Señal Móvil\n", encoding="utf-8-sig"
    )
    (entrada / "cdr_04.csv").write_text(ENCABEZADO, encoding="utf-8")
    (entrada / "otro.txt").write_text("no es un cdr", encoding="utf-8")
    (entrada / "resumen_viejo.csv").write_text("x;y\n", encoding="utf-8")
    return entrada


def test_detecta_utf8(carpeta):
    assert c.detectar_encoding(carpeta / "cdr_01.csv") == "utf-8"


def test_detecta_latin1(carpeta):
    assert c.detectar_encoding(carpeta / "cdr_02.csv") == "latin-1"


def test_detecta_bom(carpeta):
    assert c.detectar_encoding(carpeta / "cdr_03.csv") == "utf-8-sig"


def test_detecta_error_al_final(tmp_path):
    ruta = tmp_path / "cdr_tarde.csv"
    ruta.write_bytes(b"a" * 3_000_000 + "ñ".encode("latin-1"))
    assert c.detectar_encoding(ruta) == "latin-1", "Revisa todo el archivo, no solo el comienzo"


def test_resumen_de_un_archivo(carpeta):
    assert c.resumir_archivo(carpeta / "cdr_01.csv") == {
        "archivo": "cdr_01.csv",
        "registros": 3,
        "minutos_voz": 5,
        "encoding": "utf-8",
        "operadores": ["Señal Móvil", "Telefónica Perú"],
    }


def test_operadores_latin1_bien_decodificados(carpeta):
    assert c.resumir_archivo(carpeta / "cdr_02.csv")["operadores"] == ["Conexión Andina"]


def test_bom_no_afecta_el_encabezado(carpeta):
    resumen = c.resumir_archivo(carpeta / "cdr_03.csv")
    assert resumen["registros"] == 2 and resumen["minutos_voz"] == 60


def test_consolidar(carpeta, tmp_path):
    salida = tmp_path / "reporte.csv"
    resultado = c.consolidar(carpeta, salida)
    assert [a["archivo"] for a in resultado["archivos"]] == ["cdr_01.csv", "cdr_02.csv", "cdr_03.csv", "cdr_04.csv"]
    assert resultado["total_registros"] == 7
    assert resultado["total_minutos_voz"] == 66


def test_reporte_csv(carpeta, tmp_path):
    salida = tmp_path / "reporte.csv"
    c.consolidar(carpeta, salida)
    with open(salida, encoding="utf-8", newline="") as archivo:
        filas = list(csv.reader(archivo, delimiter=";"))
    assert filas[0] == ["archivo", "registros", "minutos_voz", "encoding"]
    assert filas[2] == ["cdr_02.csv", "2", "1", "latin-1"]
    assert filas[4] == ["cdr_04.csv", "0", "0", "utf-8"]
    assert filas[-1] == ["TOTAL", "7", "66", ""]
