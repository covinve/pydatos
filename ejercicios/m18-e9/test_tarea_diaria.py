"""Pruebas del ejercicio m18-e9."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import pytest

import tarea_diaria as t


@pytest.fixture
def base(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "cdr_20260902.csv").write_text("cdr_id|duracion_seg\n1|60\n2|125\n", encoding="utf-8")
    (entrada / "cdr_20260901.csv").write_text("cdr_id|duracion_seg\n1|10\n", encoding="utf-8")
    (entrada / "LEAME.txt").write_text("hola", encoding="utf-8")
    yield tmp_path
    cerrar()


def cerrar():
    """Cierra los manejadores para liberar tarea.log (en Windows un archivo abierto no se puede borrar)."""
    logger = logging.getLogger(t.LOGGER)
    for manejador in logger.handlers:
        manejador.close()
    logger.handlers.clear()


def log(base):
    for manejador in logging.getLogger(t.LOGGER).handlers:
        manejador.flush()
    return (base / "logs" / "tarea.log").read_text(encoding="utf-8")


AHORA = datetime(2026, 9, 3, 6, 0)


def test_ejecucion_correcta(base):
    assert t.ejecutar(base, AHORA) == t.OK
    resumen = json.loads((base / "salidas" / "resumen_20260903.json").read_text(encoding="utf-8"))
    assert resumen == {"fecha": "2026-09-03", "errores": [], "procesados": [
        {"archivo": "cdr_20260901.csv", "filas": 1, "segundos": 10},
        {"archivo": "cdr_20260902.csv", "filas": 2, "segundos": 185}]}
    assert sorted(a.name for a in (base / "procesados").iterdir()) == ["cdr_20260901.csv", "cdr_20260902.csv"]
    texto = log(base)
    assert "Inicio" in texto and "Fin" in texto and "cdr_20260902.csv" in texto
    assert not (base / "tarea.lock").exists(), "El bloqueo se libera al terminar"


def test_archivo_con_error(base):
    (base / "entrada" / "cdr_20260903.csv").write_text("cdr_id|duracion_seg\n1|abc\n", encoding="utf-8")
    assert t.ejecutar(base, AHORA) == t.CON_ERRORES
    assert (base / "errores" / "cdr_20260903.csv").exists()
    texto = log(base)
    assert "ERROR" in texto and "Traceback" in texto, "Usa logger.exception para incluir el traceback"
    resumen = json.loads((base / "salidas" / "resumen_20260903.json").read_text(encoding="utf-8"))
    assert resumen["errores"] == ["cdr_20260903.csv"] and len(resumen["procesados"]) == 2


def test_sin_archivos(base):
    t.ejecutar(base, AHORA)
    assert t.ejecutar(base, AHORA) == t.SIN_ARCHIVOS
    assert "WARNING" in log(base)


def test_bloqueo_tomado(base):
    (base / "tarea.lock").write_text("otro proceso", encoding="utf-8")
    assert t.ejecutar(base, AHORA) == t.EN_CURSO
    assert len(list((base / "entrada").glob("cdr_*.csv"))) == 2, "No debe procesar nada"
    assert (base / "tarea.lock").read_text(encoding="utf-8") == "otro proceso", "No borra un bloqueo ajeno vigente"
    assert "ERROR" in log(base)


def test_bloqueo_huerfano(base):
    lock = base / "tarea.lock"
    lock.write_text("proceso muerto", encoding="utf-8")
    hace_un_dia = time.time() - 24 * 3600
    os.utime(lock, (hace_un_dia, hace_un_dia))
    assert t.ejecutar(base, AHORA) == t.OK
    assert not lock.exists()
    assert "WARNING" in log(base)


def test_bloqueo_directo(tmp_path):
    ruta = tmp_path / "x.lock"
    with t.Bloqueo(ruta):
        contenido = ruta.read_text(encoding="utf-8")
        assert str(os.getpid()) in contenido
        with pytest.raises(RuntimeError):
            with t.Bloqueo(ruta):
                pass
        assert ruta.exists(), "El segundo intento no debe borrar el bloqueo del primero"
    assert not ruta.exists()
    with pytest.raises(ZeroDivisionError):
        with t.Bloqueo(ruta):
            1 / 0
    assert not ruta.exists(), "Se libera aunque haya una excepción"


def test_registro_sin_duplicados(tmp_path):
    for _ in range(3):
        logger = t.configurar_registro(tmp_path / "logs")
    assert len(logger.handlers) == 1
    logger.info("hola")
    logger.handlers[0].flush()
    assert (tmp_path / "logs" / "tarea.log").read_text(encoding="utf-8").count("hola") == 1
    cerrar()


def test_comando(tmp_path):
    cmd = t.comando_programador(Path("venv/Scripts/python.exe"), Path("tarea_diaria.py"), Path("bandeja"), "05:30")
    python = str(Path("venv/Scripts/python.exe").resolve())
    assert cmd.startswith('schtasks /Create /TN "Telco\\TareaDiaria" /SC DAILY /ST 05:30 /TR ')
    assert f'\\"{python}\\"' in cmd
    assert f'\\"{Path("bandeja").resolve()}\\""' in cmd
    assert cmd.endswith(" /F")
