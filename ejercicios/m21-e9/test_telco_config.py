"""Pruebas del ejercicio m21-e9."""

import json
import os

import pytest
from typer.testing import CliRunner

import telco_config as t

runner = CliRunner()


@pytest.fixture(autouse=True)
def sin_telco(monkeypatch, tmp_path):
    for variable in list(os.environ):
        if variable.upper().startswith("TELCO_"):
            monkeypatch.delenv(variable)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def archivos(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text('periodo = "202608"\numbral_rechazo = 3.0\nhilos = 8\ndatos = "D:/cdr"\n', encoding="utf-8")
    env = tmp_path / "local.env"
    env.write_text("TELCO_HILOS=12\nTELCO_DB_URL=postgresql://carlos:Clave123@db/fact\n", encoding="utf-8")
    return toml, env


def correr(*argumentos, env=None):
    assert t.app is not None, "Crea app = typer.Typer()"
    return runner.invoke(t.app, [str(a) for a in argumentos], env=env)


def test_valores_por_defecto():
    c = t.crear_config(None, None)
    assert (c.periodo, c.umbral_rechazo, c.hilos, c.db_url) == ("202609", 5.0, 4, None)


def test_precedencia(archivos, monkeypatch):
    toml, env = archivos
    c = t.crear_config(toml, None)
    assert (c.periodo, c.umbral_rechazo, c.hilos) == ("202608", 3.0, 8), "El TOML gana sobre los valores por defecto"
    c = t.crear_config(toml, env)
    assert c.hilos == 12, ".env gana sobre el TOML"
    monkeypatch.setenv("TELCO_HILOS", "16")
    monkeypatch.setenv("TELCO_UMBRAL_RECHAZO", "2.5")
    c = t.crear_config(toml, env, umbral_rechazo=1.5, periodo=None)
    assert (c.hilos, c.umbral_rechazo, c.periodo) == (16, 1.5, "202608"), "entorno > .env; argumentos > todo; None no cuenta"


def test_toml_con_clave_desconocida(tmp_path):
    malo = tmp_path / "malo.toml"
    malo.write_text("umbrall = 1\n", encoding="utf-8")
    with pytest.raises(Exception):
        t.crear_config(malo, None)


def test_mostrar(archivos):
    toml, env = archivos
    r = correr("mostrar", "--config", toml, "--env-file", env)
    assert r.exit_code == 0, r.output
    lineas = r.output.strip().splitlines()
    assert lineas == ["periodo = 202608", "datos = D:/cdr" if os.sep == "/" else "datos = D:\\cdr",
                      "umbral_rechazo = 3.0", "hilos = 12", "db_url = ***"]
    assert "Clave123" not in r.output


def test_mostrar_json(archivos):
    toml, env = archivos
    r = correr("mostrar", "--config", toml, "--env-file", env, "--json")
    datos = json.loads(r.output)
    assert datos["hilos"] == 12 and datos["db_url"] == "***" and datos["periodo"] == "202608"


def test_validar(archivos):
    toml, _ = archivos
    r = correr("validar", "--config", toml)
    assert r.exit_code == 0 and "Configuración válida" in r.output
    r = correr("validar", "--config", toml, env={"TELCO_HILOS": "0", "TELCO_PERIODO": "202613"})
    assert r.exit_code == 2
    assert "✗ hilos:" in r.output and "✗ periodo:" in r.output


def test_ejecutar(archivos):
    toml, env = archivos
    r = correr("ejecutar", "--config", toml, "--env-file", env, "--umbral", "1.5")
    assert r.exit_code == 0, r.output
    assert "periodo 202608 con umbral 1.5 y 12 hilos" in r.output
    r = correr("ejecutar", "--config", toml, "--periodo", "202699")
    assert r.exit_code == 2 and "✗ periodo:" in r.output


def test_sin_archivos():
    r = correr("ejecutar")
    assert r.exit_code == 0 and "periodo 202609 con umbral 5.0 y 4 hilos" in r.output
