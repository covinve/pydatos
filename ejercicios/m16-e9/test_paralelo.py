"""Pruebas del ejercicio m16-e9."""

from pathlib import Path

import pytest

import paralelo as p

CDR = Path(__file__).parent / "datos_prueba" / "cdr.csv"


@pytest.fixture(scope="module")
def carpeta(tmp_path_factory):
    """Parte cdr.csv en un archivo por día (como llegan muchas veces de los conmutadores)."""
    destino = tmp_path_factory.mktemp("diarios")
    cabecera, *filas = CDR.read_text(encoding="utf-8").splitlines()
    por_dia = {}
    for fila in filas:
        dia = fila.split("|")[5][:10].replace("/", "-")
        por_dia.setdefault(dia if dia[:4].isdigit() else "sin_fecha", []).append(fila)
    for dia, lineas in por_dia.items():
        (destino / f"cdr_{dia}.csv").write_text("\n".join([cabecera, *lineas]) + "\n", encoding="utf-8")
    (destino / "LEAME.txt").write_text("no es un CDR", encoding="utf-8")
    return destino


def esperado(filas):
    r = {"registros": len(filas), "por_tipo": {"VOZ": 0, "SMS": 0, "DATOS": 0}, "minutos": 0, "mb": 0.0}
    for f in filas:
        c = f.split("|")
        if c[3] in r["por_tipo"]:
            r["por_tipo"][c[3]] += 1
        if c[3] == "VOZ" and int(c[6]) >= 0:
            r["minutos"] += (int(c[6]) + 59) // 60
        if c[3] == "DATOS":
            r["mb"] += float(c[7])
    return r


def test_resumir_archivo():
    filas = CDR.read_text(encoding="utf-8").splitlines()[1:]
    r = p.resumir_archivo(CDR)
    e = esperado(filas)
    assert r["archivo"] == "cdr.csv"
    assert r["registros"] == e["registros"]
    assert r["por_tipo"] == e["por_tipo"]
    assert r["minutos"] == e["minutos"]
    assert abs(r["mb"] - e["mb"]) < 0.01


def test_combinar():
    a = {"archivo": "a", "registros": 2, "por_tipo": {"VOZ": 1, "SMS": 1, "DATOS": 0}, "minutos": 3, "mb": 0.0}
    b = {"archivo": "b", "registros": 1, "por_tipo": {"VOZ": 0, "SMS": 0, "DATOS": 1}, "minutos": 0, "mb": 1.5}
    assert p.combinar([a, b]) == {"archivos": 2, "registros": 3, "por_tipo": {"VOZ": 1, "SMS": 1, "DATOS": 1},
                                  "minutos": 3, "mb": 1.5}
    assert p.combinar([])["archivos"] == 0


def test_secuencial_cuadra_con_el_archivo_completo(carpeta):
    total = p.resumir_archivo(CDR)
    r = p.secuencial(carpeta)
    assert r["archivos"] == len(list(carpeta.glob("cdr_*.csv"))) > 20
    for clave in ("registros", "por_tipo", "minutos"):
        assert r[clave] == total[clave], clave
    assert abs(r["mb"] - total["mb"]) < 0.01


@pytest.mark.parametrize("procesos", [1, 2, 4])
def test_paralelo_igual_a_secuencial(carpeta, procesos):
    s = p.secuencial(carpeta)
    r = p.en_paralelo(carpeta, procesos)
    assert r["archivos"] == s["archivos"]
    assert r["por_tipo"] == s["por_tipo"] and r["minutos"] == s["minutos"] and r["registros"] == s["registros"]
    assert abs(r["mb"] - s["mb"]) < 0.001


def test_usa_procesos():
    texto = (Path(__file__).parent / "paralelo.py").read_text(encoding="utf-8")
    assert "ProcessPoolExecutor" in texto
    assert 'if __name__ == "__main__"' in texto
