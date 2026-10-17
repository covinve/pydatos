"""Pruebas del ejercicio m20-e9: el proyecto queda listo para integración continua."""

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

PROYECTO = Path(__file__).parent / "proyecto"


def ejecutar(*argumentos, cwd=PROYECTO):
    return subprocess.run([sys.executable, "-m", *argumentos], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


@pytest.fixture(scope="module")
def config():
    ruta = PROYECTO / "pyproject.toml"
    assert ruta.exists(), "Crea proyecto/pyproject.toml"
    return tomllib.loads(ruta.read_text(encoding="utf-8"))


def test_pyproject_proyecto(config):
    proyecto = config["project"]
    assert proyecto["name"] == "telco-calidad"
    assert "requires-python" in proyecto
    dev = " ".join(proyecto["optional-dependencies"]["dev"])
    for herramienta in ("pytest", "ruff", "mypy"):
        assert herramienta in dev, f"Agrega {herramienta} a [project.optional-dependencies] dev"
    assert "build-backend" in config["build-system"]


def test_pyproject_herramientas(config):
    herramientas = config["tool"]
    assert {"E", "F", "B", "I"} <= set(herramientas["ruff"]["lint"]["select"])
    assert herramientas["mypy"]["strict"] is True
    pytest_ini = herramientas["pytest"]["ini_options"]
    assert pytest_ini["testpaths"] == ["tests"]
    assert "src" in pytest_ini["pythonpath"], "pythonpath = [\"src\"] para importar el paquete sin instalarlo"


def test_ruff_check():
    r = ejecutar("ruff", "check", ".")
    assert r.returncode == 0, "ruff check encontró problemas:\n" + r.stdout


def test_ruff_format():
    r = ejecutar("ruff", "format", "--check", ".")
    assert r.returncode == 0, "Hay archivos sin formatear (ejecuta ruff format):\n" + r.stdout


def test_mypy():
    r = ejecutar("mypy", "src", "--no-incremental", "--cache-dir", os.devnull)
    assert r.returncode == 0, "mypy encontró errores:\n" + r.stdout


def test_pytest():
    r = ejecutar("pytest", "-q", "-p", "no:cacheprovider")
    assert r.returncode == 0, "Las pruebas del proyecto fallan:\n" + r.stdout[-1500:]


def test_pre_commit():
    ruta = PROYECTO / ".pre-commit-config.yaml"
    assert ruta.exists(), "Crea proyecto/.pre-commit-config.yaml"
    texto = ruta.read_text(encoding="utf-8")
    for gancho in ("ruff-pre-commit", "id: ruff", "check-added-large-files", "detect-private-key"):
        assert gancho in texto, f"Falta {gancho} en .pre-commit-config.yaml"


def test_github_actions():
    ruta = PROYECTO / ".github" / "workflows" / "pruebas.yml"
    assert ruta.exists(), "Crea proyecto/.github/workflows/pruebas.yml"
    texto = ruta.read_text(encoding="utf-8")
    assert re.search(r"^on:", texto, re.M) and "push" in texto and "pull_request" in texto
    for requisito in ("actions/checkout@", "actions/setup-python@", "ubuntu-latest", "windows-latest",
                      'pip install -e ".[dev]"', "ruff check", "mypy", "pytest"):
        assert requisito in texto, f"Falta {requisito!r} en el workflow"
