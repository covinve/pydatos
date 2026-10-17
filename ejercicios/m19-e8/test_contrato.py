"""Pruebas del ejercicio m19-e8: la MISMA batería corre contra las tres implementaciones."""

import csv
import json
from datetime import date
from pathlib import Path

import pytest

import repositorios as r

DATOS = Path(__file__).parent / "datos_prueba"
ANA = r.Cliente("3001112233", "Ana Gómez", "HOG30", "RESIDENCIAL", date(2021, 3, 4))
LUIS = r.Cliente("3001112200", "Luis Díaz", "HOG30", "RESIDENCIAL", date(2022, 7, 1))
EMPRESA = r.Cliente("3104445566", "Ñandú S.A.S.", "EMP100", "EMPRESARIAL", date(2019, 1, 15))


# Cada fábrica crea un repositorio vacío. Las de archivo devuelven también cómo "reabrirlo".
FABRICAS = {
    "memoria": lambda tmp: (r.ClientesEnMemoria(), None),
    "sqlite": lambda tmp: (r.ClientesSQLite(tmp / "clientes.db"), lambda: r.ClientesSQLite(tmp / "clientes.db")),
    "json": lambda tmp: (r.ClientesJSON(tmp / "clientes.json"), lambda: r.ClientesJSON(tmp / "clientes.json")),
}


@pytest.fixture(params=FABRICAS)
def fabrica(request, tmp_path):
    return lambda: FABRICAS[request.param](tmp_path)


@pytest.fixture
def repo(fabrica):
    return fabrica()[0]


# ---------------------------------------------------------------------------
# El contrato: vale para TODAS las implementaciones
# ---------------------------------------------------------------------------

def test_vacio(repo):
    assert repo.contar() == 0
    assert repo.del_plan("HOG30") == []


def test_guardar_y_obtener(repo):
    repo.guardar(ANA)
    obtenido = repo.obtener(ANA.linea)
    assert obtenido == ANA
    assert isinstance(obtenido.fecha_alta, date), "fecha_alta vuelve como date, no como texto"
    assert repo.contar() == 1


def test_no_encontrado(repo):
    with pytest.raises(r.ClienteNoEncontrado):
        repo.obtener("3000000000")
    assert issubclass(r.ClienteNoEncontrado, LookupError)


def test_guardar_reemplaza(repo):
    repo.guardar(ANA)
    cambiado = r.Cliente(ANA.linea, ANA.nombre, "ILIM", ANA.segmento, ANA.fecha_alta)
    repo.guardar(cambiado)
    assert repo.contar() == 1
    assert repo.obtener(ANA.linea).plan_id == "ILIM"
    assert repo.del_plan("HOG30") == []


def test_del_plan_ordenado(repo):
    for c in (ANA, EMPRESA, LUIS):
        repo.guardar(c)
    assert repo.del_plan("HOG30") == [LUIS, ANA]
    assert repo.del_plan("EMP100") == [EMPRESA]


def test_tildes_y_enes(repo):
    repo.guardar(EMPRESA)
    assert repo.obtener(EMPRESA.linea).nombre == "Ñandú S.A.S."


def test_cargar_csv(repo):
    with open(DATOS / "clientes.csv", encoding="latin-1", newline="") as f:
        filas = list(csv.DictReader(f))
    assert r.cargar_csv(repo, DATOS / "clientes.csv") == len(filas)
    assert repo.contar() == len(filas)
    primero = repo.obtener(filas[0]["linea"])
    assert primero.nombre == filas[0]["nombre"]
    assert primero.fecha_alta == date.fromisoformat(filas[0]["fecha_alta"])
    assert len(repo.del_plan("HOG30")) == sum(1 for f in filas if f["plan_id"] == "HOG30")


# ---------------------------------------------------------------------------
# Persistencia: solo para las implementaciones con archivo
# ---------------------------------------------------------------------------

def test_persiste(fabrica):
    repo, reabrir = fabrica()
    if reabrir is None:
        pytest.skip("La memoria no persiste")
    repo.guardar(ANA)
    repo.guardar(EMPRESA)
    otro = reabrir()
    assert otro.contar() == 2
    assert otro.obtener(EMPRESA.linea) == EMPRESA


def test_json_legible_y_atomico(tmp_path):
    repo = r.ClientesJSON(tmp_path / "clientes.json")
    repo.guardar(EMPRESA)
    texto = (tmp_path / "clientes.json").read_text(encoding="utf-8")
    assert "Ñandú" in texto, "Usa ensure_ascii=False"
    assert json.loads(texto)[0]["fecha_alta"] == "2019-01-15"
    assert [p.name for p in tmp_path.iterdir()] == ["clientes.json"], "No deben quedar archivos temporales"
    codigo = (Path(__file__).parent / "repositorios.py").read_text(encoding="utf-8")
    assert ".replace(" in codigo, "Escribe a un temporal y usa Path.replace()"
