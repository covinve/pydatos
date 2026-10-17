"""Pruebas del ejercicio m21-e7."""

import os

import pytest
from pydantic import ValidationError

import config_pipeline as cp


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch, tmp_path):
    """Cada prueba en una carpeta vacía y sin variables TELCO_ del computador."""
    for variable in list(os.environ):
        if variable.upper().startswith("TELCO_"):
            monkeypatch.delenv(variable)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cdr").mkdir()
    return tmp_path


def errores(excepcion):
    return {e["loc"][0] for e in excepcion.value.errors()}


def test_minimo_y_valores_por_defecto(monkeypatch):
    monkeypatch.setenv("TELCO_DATOS", "cdr")
    monkeypatch.setenv("TELCO_PERIODO", "202609")
    c = cp.cargar()
    assert c.datos.name == "cdr" and c.periodo == "202609"
    assert (c.salidas.name, c.umbral_rechazo, c.memoria_duckdb, c.hilos, c.correos_alerta, c.db_url) == \
        ("salidas", 5.0, "4GB", 4, [], None)


def test_obligatorios():
    with pytest.raises(ValidationError) as e:
        cp.cargar()
    assert errores(e) == {"datos", "periodo"}


def test_desde_env_file(entorno_limpio):
    (entorno_limpio / "local.env").write_text(
        "TELCO_DATOS=cdr\nTELCO_PERIODO=202612\nTELCO_HILOS=8\nTELCO_MEMORIA_DUCKDB=8gb\n"
        'TELCO_CORREOS_ALERTA=["ana@telco.co","luis@telco.co"]\nOTRA_COSA=1\n', encoding="utf-8")
    c = cp.cargar(env_file="local.env")
    assert (c.periodo, c.hilos, c.memoria_duckdb) == ("202612", 8, "8GB")
    assert c.correos_alerta == ["ana@telco.co", "luis@telco.co"]


def test_precedencia(entorno_limpio, monkeypatch):
    (entorno_limpio / ".env").write_text("TELCO_DATOS=cdr\nTELCO_PERIODO=202609\nTELCO_UMBRAL_RECHAZO=3\n", encoding="utf-8")
    assert cp.cargar().umbral_rechazo == 3.0, "Por defecto lee .env"
    monkeypatch.setenv("TELCO_UMBRAL_RECHAZO", "2.5")
    assert cp.cargar().umbral_rechazo == 2.5, "El entorno gana sobre .env"
    assert cp.cargar(umbral_rechazo=1.0).umbral_rechazo == 1.0, "Los sobrescritos ganan sobre todo"
    assert cp.cargar(umbral_rechazo=None).umbral_rechazo == 2.5, "None = no lo indicó"
    assert cp.cargar(env_file=None, datos="cdr", periodo="202601").umbral_rechazo == 2.5


@pytest.mark.parametrize("campo, valor", [
    ("datos", "no_existe"), ("periodo", "202613"), ("periodo", "2026-09"), ("umbral_rechazo", "150"),
    ("memoria_duckdb", "muchos"), ("memoria_duckdb", "8TB"), ("hilos", "0"), ("correos_alerta", '["sin-arroba"]'),
])
def test_validaciones(monkeypatch, campo, valor):
    monkeypatch.setenv("TELCO_DATOS", "cdr")
    monkeypatch.setenv("TELCO_PERIODO", "202609")
    monkeypatch.setenv(f"TELCO_{campo.upper()}", valor)
    with pytest.raises(ValidationError) as e:
        cp.cargar()
    assert errores(e) == {campo}


def test_secreto(monkeypatch):
    monkeypatch.setenv("TELCO_DB_URL", "postgresql://carlos:Clave123@db/fact")
    c = cp.cargar(datos="cdr", periodo="202609")
    assert "Clave123" not in repr(c) and "Clave123" not in str(c)
    assert c.db_url.get_secret_value().endswith("@db/fact")
    r = c.resumen()
    assert r["db_url"] == "***" and "Clave123" not in str(r)
    assert r["hilos"] == "4" and r["correos_alerta"] == ""


def test_inmutable():
    c = cp.cargar(datos="cdr", periodo="202609")
    with pytest.raises(ValidationError):
        c.hilos = 10
