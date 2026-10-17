"""Pruebas del ejercicio m08-e7: romper la importación circular."""

import ast
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
PAQUETE = CARPETA / "tarifacion"
sys.path.insert(0, str(CARPETA))


def imports_del_paquete(archivo):
    arbol = ast.parse((PAQUETE / archivo).read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.removeprefix("tarifacion."))
        elif isinstance(nodo, ast.Import):
            modulos |= {a.name.removeprefix("tarifacion.") for a in nodo.names}
    return modulos


def test_el_paquete_se_importa():
    import tarifacion  # noqa: F401


def test_reporte_linea():
    from tarifacion import reporte_linea

    assert reporte_linea("3001234567", [("LOCAL", 125), ("INTERNACIONAL", 61)]) == "3001234567: 2 llamadas · $2.200"


def test_describir_cobro():
    from tarifacion.reglas import describir_cobro

    assert describir_cobro("NACIONAL", 3600) == "nacional 3600 s → $7.200"


def test_existe_formato():
    assert (PAQUETE / "formato.py").exists(), "Mueve formatear_pesos a tarifacion/formato.py"
    from tarifacion.formato import formatear_pesos

    assert formatear_pesos(1234567) == "$1.234.567"


def test_dependencias_en_una_direccion():
    assert "reportes" not in imports_del_paquete("reglas.py"), "reglas.py no debe importar reportes"
    assert not imports_del_paquete("formato.py") & {"reglas", "reportes"}, "formato.py no debe importar a nadie del paquete"


def test_sin_imports_escondidos_en_funciones():
    for archivo in ("reglas.py", "reportes.py"):
        arbol = ast.parse((PAQUETE / archivo).read_text(encoding="utf-8"))
        for funcion in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
            assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(funcion)), (
                f"{archivo}: no escondas el import dentro de {funcion.name}(); reorganiza los módulos"
            )
