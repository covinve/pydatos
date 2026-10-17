"""Pruebas de arquitectura y de entrega del Proyecto 3."""

import ast
from pathlib import Path

import pytest

PROYECTO = Path(__file__).resolve().parents[1]
SRC = PROYECTO / "src" / "telco_pipeline"
REPOSITORIO = PROYECTO.parents[1]
PUROS = {"__future__", "dataclasses", "math", "typing", "numpy", "pandas", "sklearn.ensemble"}


def importa(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres |= {a.name for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            nombres.add(f"telco_pipeline.{nodo.module}" if nodo.level else nodo.module)
    return nombres


@pytest.mark.parametrize("modulo", ["facturacion", "conciliacion", "anomalias"])
def test_logica_pura(modulo):
    archivo = SRC / f"{modulo}.py"
    sobran = importa(archivo) - PUROS
    assert not sobran, f"{modulo}.py es lógica pura: no debería importar {sobran}"
    texto = archivo.read_text(encoding="utf-8")
    for prohibido in ("open(", "print(", "read_csv", "to_csv", "logging"):
        assert prohibido not in texto, f"{modulo}.py no debe usar {prohibido}"


def test_solo_la_cli_y_el_pipeline_conocen_la_configuracion():
    for archivo in SRC.glob("*.py"):
        if archivo.stem in ("config", "pipeline", "cli"):
            continue
        assert "telco_pipeline.config" not in importa(archivo), f"{archivo.name} no debe depender de config"


def test_sin_iterrows_sobre_cdr():
    for archivo in SRC.glob("*.py"):
        if archivo.stem == "reporte":
            continue
        texto = archivo.read_text(encoding="utf-8")
        assert ".iterrows(" not in texto and ".apply(" not in texto, f"{archivo.name}: vectoriza, no recorras filas"


# --- entregables (fallan hasta que los crees) --------------------------------------------------

def test_dockerfile():
    ruta = PROYECTO / "Dockerfile"
    assert ruta.exists(), "Crea proyectos/p3-pipeline/Dockerfile"
    texto = ruta.read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in texto and "USER " in texto
    assert 'ENTRYPOINT ["telco"' in texto, 'El contenedor ejecuta la CLI: ENTRYPOINT ["telco", ...]'
    ignorar = (PROYECTO / ".dockerignore").read_text(encoding="utf-8")
    assert "datos_prueba" in ignorar and ".env" in ignorar


def test_integracion_continua():
    flujos = list((REPOSITORIO / ".github" / "workflows").glob("*.y*ml"))
    textos = [f.read_text(encoding="utf-8") for f in flujos]
    assert any("p3-pipeline" in t and "pytest" in t for t in textos), \
        "Crea un workflow en .github/workflows/ (en la raíz del repositorio) que pruebe proyectos/p3-pipeline"


def test_readme():
    texto = (PROYECTO / "README.md").read_text(encoding="utf-8")
    for seccion in ("## Instalación", "## Uso", "## Configuración", "## Docker", "## Arquitectura", "## Tiempos"):
        assert seccion in texto, f"Falta la sección {seccion} en README.md"
