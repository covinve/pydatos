"""Pruebas del ejercicio m22-e8. Las de Docker solo corren si Docker funciona en este equipo."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

CARPETA = Path(__file__).parent
PROYECTO = "curso-pydatos-m22-e8"


@pytest.fixture(scope="module")
def compose():
    return yaml.safe_load((CARPETA / "compose.yaml").read_text(encoding="utf-8"))


def entorno(servicio):
    e = servicio.get("environment", {})
    return dict(v.split("=", 1) for v in e) if isinstance(e, list) else e


def test_servicio_bd(compose):
    bd = compose["services"]["bd"]
    assert str(bd["image"]).startswith("postgres:16")
    e = entorno(bd)
    assert e["POSTGRES_DB"] == "facturacion" and e["POSTGRES_USER"] == "telco"
    assert re.fullmatch(r"\$\{PG_PASSWORD:\?.+\}", str(e["POSTGRES_PASSWORD"])), \
        "La contraseña sale de ${PG_PASSWORD:?mensaje}, nunca escrita en el archivo"
    assert any(str(v).startswith("pgdata:/var/lib/postgresql/data") for v in bd["volumes"])
    prueba = " ".join(bd["healthcheck"]["test"]) if isinstance(bd["healthcheck"]["test"], list) else bd["healthcheck"]["test"]
    assert "pg_isready" in prueba


def test_servicio_app(compose):
    app = compose["services"]["app"]
    assert app["build"] in (".", {"context": "."})
    assert app["depends_on"]["bd"]["condition"] == "service_healthy"
    url = str(entorno(app)["TELCO_DB_URL"])
    assert url.startswith("postgresql+psycopg://telco:${PG_PASSWORD}@bd:5432/facturacion"), \
        "Usa el nombre del servicio (bd) y el puerto interno 5432"
    assert any(str(v).replace("\\", "/") in ("./datos_prueba:/datos:ro",) for v in app["volumes"])


def test_volumen_con_nombre(compose):
    assert "pgdata" in compose["volumes"]


def test_env_example():
    ruta = CARPETA / ".env.example"
    assert ruta.exists(), "Crea .env.example para que otros sepan qué definir"
    assert re.search(r"^PG_PASSWORD=", ruta.read_text(encoding="utf-8"), re.M)


def docker_disponible():
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


@pytest.mark.skipif(not docker_disponible(), reason="Docker no está disponible en este equipo")
def test_levanta_y_carga():
    base = ["docker", "compose", "-p", PROYECTO]
    variables = {**os.environ, "PG_PASSWORD": "clave-de-prueba"}
    try:
        r = subprocess.run([*base, "up", "--build", "--abort-on-container-exit", "--exit-code-from", "app"],
                           cwd=CARPETA, env=variables, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=900)
        assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
        assert "40 clientes cargados en PostgreSQL" in r.stdout
    finally:
        subprocess.run([*base, "down", "-v", "--rmi", "local"], cwd=CARPETA, env=variables, capture_output=True, timeout=300)


def test_sin_password_falla_con_mensaje(tmp_path):
    if not docker_disponible():
        pytest.skip("Docker no está disponible en este equipo")
    variables = {k: v for k, v in os.environ.items() if k != "PG_PASSWORD"}
    vacio = tmp_path / "vacio.env"
    vacio.write_text("", encoding="utf-8")
    r = subprocess.run(["docker", "compose", "-p", PROYECTO, "--env-file", str(vacio), "config"], cwd=CARPETA,
                       env=variables, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode != 0 and "PG_PASSWORD" in r.stderr
