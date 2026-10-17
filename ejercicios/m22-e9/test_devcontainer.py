"""Pruebas del ejercicio m22-e9."""

import json
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

import esperar_servicio as e

CARPETA = Path(__file__).parent


# ---------------------------------------------------------------------------
# devcontainer.json
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dev():
    ruta = CARPETA / ".devcontainer" / "devcontainer.json"
    assert ruta.exists(), "Crea .devcontainer/devcontainer.json"
    sin_comentarios = "\n".join(l for l in ruta.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("//"))
    return json.loads(sin_comentarios)


def test_imagen_y_nombre(dev):
    assert dev["name"]
    assert dev["image"].startswith("mcr.microsoft.com/devcontainers/python:") and "3.12" in dev["image"]


def test_docker_dentro(dev):
    assert any("docker-in-docker" in f for f in dev.get("features", {})), \
        "Agrega la feature ghcr.io/devcontainers/features/docker-in-docker para usar Docker en Codespaces"


def test_instala_librerias(dev):
    assert "pip install -r requirements.txt" in dev["postCreateCommand"]


def test_extensiones(dev):
    extensiones = dev["customizations"]["vscode"]["extensions"]
    for necesaria in ("ms-python.python", "charliermarsh.ruff", "ms-toolsai.jupyter"):
        assert necesaria in extensiones


def test_puerto(dev):
    assert 5432 in dev["forwardPorts"]


# ---------------------------------------------------------------------------
# esperar_servicio.py
# ---------------------------------------------------------------------------

def test_destino():
    assert e.destino("bd:5432") == ("bd", 5432)
    assert e.destino("localhost:8000") == ("localhost", 8000)
    for malo in ("bd", "bd:abc", "bd:0", "bd:70000", ":5432"):
        with pytest.raises(ValueError):
            e.destino(malo)


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def servidor_tardio(puerto, demora):
    """Empieza a escuchar en `puerto` después de `demora` segundos (como PostgreSQL al arrancar)."""
    listo = threading.Event()

    def correr():
        time.sleep(demora)
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", puerto))
            s.listen()
            s.settimeout(5)
            listo.set()
            try:
                while True:
                    conexion, _ = s.accept()
                    conexion.close()
            except OSError:
                pass

    threading.Thread(target=correr, daemon=True).start()
    return listo


def test_espera_hasta_que_responde():
    puerto = puerto_libre()
    servidor_tardio(puerto, 1.0)
    segundos = e.esperar("127.0.0.1", puerto, timeout=10, intervalo=0.2)
    assert 0.8 <= segundos < 5


def test_timeout_con_reloj_falso():
    puerto = puerto_libre()
    ahora = [0.0]
    esperas = []

    def dormir(s):
        esperas.append(s)
        ahora[0] += s

    with pytest.raises(TimeoutError, match=f"127.0.0.1:{puerto}"):
        e.esperar("127.0.0.1", puerto, timeout=3, intervalo=1, reloj=lambda: ahora[0], dormir=dormir)
    assert 3 <= len(esperas) <= 4 and set(esperas) == {1}


def test_main_ejecuta_el_comando(capsys):
    puerto = puerto_libre()
    servidor_tardio(puerto, 0).wait(5)
    codigo = e.main([f"127.0.0.1:{puerto}", "--timeout", "5", "--", sys.executable, "-c", "import sys; sys.exit(3)"])
    assert codigo == 3, "Devuelve el código de salida del comando"
    assert f"127.0.0.1:{puerto} disponible en" in capsys.readouterr().out


def test_main_sin_comando():
    puerto = puerto_libre()
    servidor_tardio(puerto, 0).wait(5)
    assert e.main([f"127.0.0.1:{puerto}"]) == 0


def test_main_timeout(capsys):
    assert e.main([f"127.0.0.1:{puerto_libre()}", "--timeout", "0.5"]) == 1
    assert "127.0.0.1" in capsys.readouterr().err
