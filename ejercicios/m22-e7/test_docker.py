"""Pruebas del ejercicio m22-e7.

Las pruebas estáticas corren siempre. Las que construyen y ejecutan la imagen solo corren si Docker
está instalado y funcionando (en casa o en Codespaces); en la oficina se saltan.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CARPETA = Path(__file__).parent
IMAGEN = "curso-pydatos-m22-e7:prueba"
sys.path.insert(0, str(CARPETA))

from app.resumen import resumir  # noqa: E402


def instrucciones():
    resultado, actual = [], []
    for linea in (CARPETA / "Dockerfile").read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        actual.append(limpia.rstrip("\\").strip())
        if not limpia.endswith("\\"):
            nombre, _, args = " ".join(actual).partition(" ")
            resultado.append((nombre.upper(), args.strip()))
            actual = []
    return resultado


def posicion(nombre, condicion=lambda a: True):
    return next((i for i, (n, a) in enumerate(instrucciones()) if n == nombre and condicion(a)), None)


# ---------------------------------------------------------------------------
# Revisión estática del Dockerfile
# ---------------------------------------------------------------------------

def test_imagen_base():
    froms = [a for n, a in instrucciones() if n == "FROM"]
    assert froms, "Falta FROM"
    imagen = froms[0].split()[0]
    assert imagen.startswith("python:3.12") and "slim" in imagen, "Usa python:3.12-slim (o una variante slim de 3.12)"


def test_variables_de_python():
    envs = " ".join(a for n, a in instrucciones() if n == "ENV")
    assert "PYTHONUNBUFFERED=1" in envs and "PYTHONDONTWRITEBYTECODE=1" in envs


def test_orden_de_capas():
    workdir = posicion("WORKDIR")
    copia_req = posicion("COPY", lambda a: "requirements.txt" in a)
    instalar = posicion("RUN", lambda a: "pip install" in a)
    copia_app = posicion("COPY", lambda a: a.split()[0].rstrip("/") == "app")
    assert None not in (workdir, copia_req, instalar, copia_app), \
        "Necesitas WORKDIR, COPY requirements.txt, RUN pip install y COPY app/"
    assert workdir < copia_req < instalar < copia_app, "Orden: WORKDIR, requirements, pip install y después el código"
    run = instrucciones()[instalar][1]
    assert "--no-cache-dir" in run and "-r requirements.txt" in run
    assert posicion("COPY", lambda a: a.split()[0] == ".") is None, "No copies todo el proyecto (COPY . ...): solo lo necesario"


def test_usuario_y_entrada():
    usuarios = [a for n, a in instrucciones() if n == "USER"]
    assert usuarios and usuarios[-1] not in ("root", "0"), "Corre con un usuario sin privilegios"
    entrada = [a for n, a in instrucciones() if n == "ENTRYPOINT"]
    assert entrada and json.loads(entrada[-1]) == ["python", "-m", "app.resumen"], \
        'ENTRYPOINT ["python", "-m", "app.resumen"]'


def test_dockerignore():
    ruta = CARPETA / ".dockerignore"
    assert ruta.exists(), "Crea .dockerignore"
    lineas = {l.strip().strip("/") for l in ruta.read_text(encoding="utf-8").splitlines()}
    for necesario in ("datos_prueba", "salidas", ".env", ".venv", "**/__pycache__"):
        assert necesario in lineas, f"Agrega {necesario} a .dockerignore"


# ---------------------------------------------------------------------------
# Con Docker de verdad
# ---------------------------------------------------------------------------

def docker_disponible():
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


con_docker = pytest.mark.skipif(not docker_disponible(), reason="Docker no está disponible en este equipo")


def docker(*argumentos, timeout=600):
    return subprocess.run(["docker", *argumentos], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


@pytest.fixture(scope="module")
def imagen():
    r = docker("build", "-t", IMAGEN, str(CARPETA))
    assert r.returncode == 0, "docker build falló:\n" + r.stderr[-2000:]
    yield IMAGEN
    docker("rmi", "-f", IMAGEN)


@con_docker
def test_ejecuta_con_volumenes(imagen, tmp_path):
    r = docker("run", "--rm", "-v", f"{CARPETA / 'datos_prueba'}:/datos:ro", "-v", f"{tmp_path}:/salidas", imagen)
    assert r.returncode == 0, r.stderr
    obtenido = json.loads((tmp_path / "resumen.json").read_text(encoding="utf-8"))
    assert obtenido == resumir(CARPETA / "datos_prueba" / "cdr.csv")


@con_docker
def test_sin_volumen_explica_el_error(imagen):
    r = docker("run", "--rm", imagen)
    assert r.returncode == 2 and "volumen" in r.stderr


@con_docker
def test_no_corre_como_root(imagen):
    r = docker("run", "--rm", "--entrypoint", "id", imagen, "-u")
    assert r.stdout.strip() != "0"


@con_docker
def test_la_imagen_no_tiene_datos(imagen):
    r = docker("run", "--rm", "--entrypoint", "sh", imagen, "-c", "ls -a /app")
    contenido = r.stdout.split()
    assert "datos_prueba" not in contenido and "test_docker.py" not in contenido
