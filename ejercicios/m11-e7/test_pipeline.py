"""Pruebas del ejercicio m11-e7."""

import inspect
import json
import tracemalloc
from pathlib import Path

import pipeline

DATOS = Path(__file__).parent / "datos_prueba"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))["cdr"]
CLAVES = ["registros_totales", "registros_validos", "errores", "minutos_nacionales",
          "minutos_internacionales", "mb_totales", "sms_totales"]


def test_resultado_cuadra_con_esperado():
    resumen = pipeline.resumir_cdr(DATOS / "cdr.csv", DATOS / "clientes.csv")
    for clave in CLAVES:
        if clave == "mb_totales":
            assert abs(resumen[clave] - ESPERADO[clave]) < 0.01
        else:
            assert resumen[clave] == ESPERADO[clave], f"{clave}: {resumen[clave]} != {ESPERADO[clave]}"


def test_usa_generadores():
    generadores = [n for n, f in inspect.getmembers(pipeline, inspect.isfunction) if inspect.isgeneratorfunction(f)]
    assert len(generadores) >= 3, f"Divide el proceso en al menos 3 etapas generadoras; encontré {generadores}"


def test_memoria_constante(tmp_path):
    """Con un archivo 50 veces más grande, el pico de memoria no debe crecer."""
    lineas = (DATOS / "cdr.csv").read_text(encoding="utf-8").splitlines()
    grande = tmp_path / "cdr.csv"
    with open(grande, "w", encoding="utf-8") as salida:
        salida.write(lineas[0] + "\n")
        for copia in range(50):
            for linea in lineas[1:]:
                cdr_id, resto = linea.split("|", 1)
                salida.write(f"{int(cdr_id) + copia * 1_000_000}|{resto}\n")
    tracemalloc.start()
    resumen = pipeline.resumir_cdr(grande, DATOS / "clientes.csv")
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert resumen["registros_totales"] == 50 * ESPERADO["registros_totales"]
    assert pico < 8_000_000, f"El pico de memoria fue {pico / 1e6:.1f} MB: ¿estás guardando registros en listas?"
