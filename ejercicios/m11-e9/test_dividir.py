"""Pruebas del ejercicio m11-e9."""

import ast
import gzip
from pathlib import Path

import dividir as d

ENCABEZADO = "cdr_id|tipo|duracion_seg\n"


def crear(tmp_path, n, gz=False):
    texto = ENCABEZADO + "".join(f"{i}|VOZ|{i * 10}\n" for i in range(1, n + 1))
    if gz:
        ruta = tmp_path / "cdr.csv.gz"
        with gzip.open(ruta, "wt", encoding="utf-8") as f:
            f.write(texto)
    else:
        ruta = tmp_path / "cdr.csv"
        ruta.write_text(texto, encoding="utf-8")
    return ruta


def leer(ruta):
    if ruta.suffix == ".gz":
        with gzip.open(ruta, "rt", encoding="utf-8") as f:
            return f.read()
    return ruta.read_text(encoding="utf-8")


def test_divide_en_partes(tmp_path):
    partes = d.dividir(crear(tmp_path, 10), 4, tmp_path / "salida")
    assert [p.name for p in partes] == ["cdr_parte_001.csv", "cdr_parte_002.csv", "cdr_parte_003.csv"]
    contenidos = [leer(p) for p in partes]
    assert all(c.startswith(ENCABEZADO) for c in contenidos)
    assert [c.count("\n") - 1 for c in contenidos] == [4, 4, 2]
    assert contenidos[2].endswith("10|VOZ|100\n")


def test_division_exacta(tmp_path):
    partes = d.dividir(crear(tmp_path, 8), 4, tmp_path / "salida")
    assert len(partes) == 2, "Si los registros caben exacto, no debe quedar una parte vacía"


def test_archivo_sin_registros(tmp_path):
    partes = d.dividir(crear(tmp_path, 0), 4, tmp_path / "salida")
    assert len(partes) == 1 and leer(partes[0]) == ENCABEZADO


def test_lee_gzip(tmp_path):
    partes = d.dividir(crear(tmp_path, 5, gz=True), 3, tmp_path / "salida")
    assert [p.name for p in partes] == ["cdr_parte_001.csv", "cdr_parte_002.csv"]
    assert leer(partes[1]) == ENCABEZADO + "4|VOZ|40\n5|VOZ|50\n"


def test_escribe_gzip(tmp_path):
    partes = d.dividir(crear(tmp_path, 5), 3, tmp_path / "salida", comprimir=True)
    assert [p.name for p in partes] == ["cdr_parte_001.csv.gz", "cdr_parte_002.csv.gz"]
    assert leer(partes[0]) == ENCABEZADO + "1|VOZ|10\n2|VOZ|20\n3|VOZ|30\n"


def test_crea_la_carpeta(tmp_path):
    d.dividir(crear(tmp_path, 2), 1, tmp_path / "no" / "existe")
    assert (tmp_path / "no" / "existe" / "cdr_parte_002.csv").exists()


def test_no_carga_todo():
    arbol = ast.parse((Path(__file__).parent / "dividir.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
            assert nodo.func.attr not in ("read", "readlines", "read_text"), "Recorre el archivo línea por línea"
