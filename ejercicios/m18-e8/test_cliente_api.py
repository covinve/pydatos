"""Pruebas del ejercicio m18-e8: un servidor local simula la API (con sus fallos)."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest
import requests

import cliente_api as c

TOKEN = "secreto-de-prueba"
TARIFAS = {"HOG30": {"plan_id": "HOG30", "tarifa_minuto": 120, "tarifa_mb": 18}}
CONSUMOS = [{"linea": f"300{i:07d}", "minutos": (i * 37) % 900} for i in range(95)]


class Estado:
    def __init__(self):
        self.peticiones = []
        self.fallos = {}            # (ruta, pagina) -> lista de respuestas a dar antes de la buena
        self.ajustes = {}


def crear_manejador(estado):
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def responder(self, codigo, cuerpo, cabeceras=None):
            datos = json.dumps(cuerpo).encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            for k, v in (cabeceras or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(datos)

        def autorizado(self):
            if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                self.responder(401, {"error": "token inválido"})
                return False
            return True

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            estado.peticiones.append(("GET", url.path, q))
            if not self.autorizado():
                return
            clave = (url.path, q.get("pagina"))
            if estado.fallos.get(clave):
                codigo, cabeceras = estado.fallos[clave].pop(0)
                return self.responder(codigo, {"error": "falla simulada"}, cabeceras)
            if url.path.startswith("/tarifas/"):
                plan = url.path.rsplit("/", 1)[1]
                if plan == "LENTO":
                    time.sleep(1.5)
                if plan in TARIFAS:
                    return self.responder(200, TARIFAS[plan])
                return self.responder(404, {"error": "no existe"})
            if url.path == "/consumos":
                pagina, tamano = int(q["pagina"]), int(q.get("tamano", 20))
                total = -(-len(CONSUMOS) // tamano) if q.get("periodo") == "202609" else 0
                datos = CONSUMOS[(pagina - 1) * tamano: pagina * tamano] if q.get("periodo") == "202609" else []
                return self.responder(200, {"datos": datos, "pagina": pagina, "total_paginas": total})
            self.responder(404, {"error": "ruta"})

        def do_POST(self):
            url = urlparse(self.path)
            cuerpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            estado.peticiones.append(("POST", url.path, cuerpo))
            if not self.autorizado():
                return
            if estado.fallos.get((url.path, None)):
                codigo, cabeceras = estado.fallos[(url.path, None)].pop(0)
                # el servidor alcanza a registrar el ajuste, pero la respuesta "se pierde"
                estado.ajustes.setdefault(self.headers.get("Idempotency-Key"), cuerpo)
                return self.responder(codigo, {"error": "falla simulada"}, cabeceras)
            clave = self.headers.get("Idempotency-Key")
            if not clave:
                return self.responder(400, {"error": "falta Idempotency-Key"})
            nuevo = clave not in estado.ajustes
            estado.ajustes.setdefault(clave, cuerpo)
            self.responder(201 if nuevo else 200, {"ajuste": estado.ajustes[clave], "repetido": not nuevo})

    return Manejador


@pytest.fixture(autouse=True)
def sin_proxy(monkeypatch):
    """En la oficina puede haber un proxy configurado: el servidor de prueba es local."""
    for variable in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")


@pytest.fixture
def api():
    estado = Estado()
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), crear_manejador(estado))
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    estado.url = f"http://127.0.0.1:{servidor.server_address[1]}"
    yield estado
    servidor.shutdown()
    servidor.server_close()


def cliente(api, **opciones):
    esperas = []
    opciones.setdefault("token", TOKEN)
    return c.ClienteAPI(api.url, dormir=esperas.append, **opciones), esperas


def test_token_de_variable_de_entorno(api, monkeypatch):
    monkeypatch.setenv("TELCO_API_TOKEN", TOKEN)
    assert c.ClienteAPI(api.url).tarifa("HOG30")["tarifa_minuto"] == 120
    monkeypatch.delenv("TELCO_API_TOKEN")
    with pytest.raises(ValueError):
        c.ClienteAPI(api.url)


def test_tarifa(api):
    cli, esperas = cliente(api)
    assert cli.tarifa("HOG30") == TARIFAS["HOG30"]
    with pytest.raises(LookupError):
        cli.tarifa("NOEXISTE")
    assert esperas == [], "Un 404 no se reintenta"


def test_token_invalido(api):
    cli, esperas = cliente(api, token="malo")
    with pytest.raises(PermissionError):
        cli.tarifa("HOG30")
    assert len(api.peticiones) == 1 and esperas == []


def test_paginacion(api):
    cli, _ = cliente(api)
    datos = list(cli.consumos("202609"))
    assert datos == CONSUMOS
    paginas = [q["pagina"] for metodo, ruta, q in api.peticiones]
    assert paginas == ["1", "2", "3", "4", "5"]
    assert list(cli.consumos("199901")) == []
    assert len(list(cli.consumos("202609", tamano=50))) == 95


def test_paginacion_perezosa(api):
    cli, _ = cliente(api)
    g = cli.consumos("202609")
    next(g)
    assert len(api.peticiones) == 1


def test_reintentos(api):
    api.fallos[("/consumos", "2")] = [(429, {"Retry-After": "3"})]
    api.fallos[("/consumos", "4")] = [(503, {}), (502, {})]
    cli, esperas = cliente(api, base=0.5)
    assert list(cli.consumos("202609")) == CONSUMOS
    assert esperas == [3.0, 0.5, 1.0]


def test_reintentos_agotados(api):
    api.fallos[("/tarifas/HOG30", None)] = [(500, {})] * 5
    cli, esperas = cliente(api, intentos=3)
    with pytest.raises(requests.HTTPError):
        cli.tarifa("HOG30")
    assert esperas == [1.0, 2.0]


def test_timeout(api):
    cli, esperas = cliente(api, timeout=0.3, intentos=2)
    with pytest.raises(requests.Timeout):
        cli.tarifa("LENTO")
    assert esperas == [1.0], "Un timeout se reintenta"


def test_ajuste_idempotente(api):
    api.fallos[("/ajustes", None)] = [(503, {})]
    cli, esperas = cliente(api)
    r = cli.registrar_ajuste("F001", -5000, "reclamo 123")
    assert esperas == [1.0]
    assert r["ajuste"] == {"factura_id": "F001", "valor": -5000, "motivo": "reclamo 123"}
    assert len(api.ajustes) == 1, "El reintento no duplicó el ajuste"
    cli.registrar_ajuste("F001", -5000, "reclamo 123")
    assert len(api.ajustes) == 1
    cli.registrar_ajuste("F001", -1000, "reclamo 124")
    assert len(api.ajustes) == 2
