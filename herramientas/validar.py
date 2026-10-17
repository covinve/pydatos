"""Valida que los ejercicios del curso estén bien construidos.

Para cada ejercicio de la página y cada reto de las lecciones comprueba que:
  - la solución oficial pasa todas las pruebas, y
  - el código inicial NO las pasa (si las pasara, el ejercicio no enseñaría nada).
También ejecuta los bloques `pyrun` de las lecciones y avisa si alguno falla.

Uso:
    python herramientas/construir.py
    python herramientas/validar.py            # todo el curso
    python herramientas/validar.py m05        # solo un módulo
    python herramientas/validar.py m05 --retos   # solo los retos de las lecciones
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "assets" / "py"))

import evaluador  # noqa: E402
from construir import extraer_retos  # noqa: E402

ARCHIVOS_LECCION = ["muestra/cdr.csv", "muestra/clientes.csv", "muestra/planes.csv", "muestra/facturas.csv"]


def preparar_carpeta(archivos: list[str]) -> Path:
    carpeta = Path(tempfile.mkdtemp(prefix="pydatos_"))
    for archivo in archivos:
        shutil.copy(RAIZ / "contenido" / "datos" / archivo, carpeta / Path(archivo).name)
    return carpeta


def correr(codigo: str, ejercicio: dict, modo: str = "probar") -> dict:
    carpeta = preparar_carpeta(ejercicio.get("archivos", []))
    anterior = os.getcwd()
    os.chdir(carpeta)
    try:
        return evaluador.ejecutar(codigo, modo, ejercicio.get("pruebas", ""), ejercicio.get("preparacion", ""))
    finally:
        os.chdir(anterior)
        shutil.rmtree(carpeta, ignore_errors=True)


def validar_ejercicio(ejercicio: dict) -> list[str]:
    problemas = []
    inicio = time.perf_counter()
    resultado = correr(ejercicio["solucion"], ejercicio)
    duracion = time.perf_counter() - inicio
    if resultado["sintaxis"] or resultado["error"]:
        problemas.append(f"la solución falla: {resultado['error']}")
    elif not resultado["pruebas"]:
        problemas.append("no hay funciones prueba_*")
    else:
        for prueba in resultado["pruebas"]:
            if not prueba["ok"]:
                problemas.append(f"la solución no pasa «{prueba['nombre']}»: {prueba['mensaje']}")
    if duracion > 8:
        problemas.append(f"la solución tarda {duracion:.1f} s (en el navegador será más lento)")

    inicial = correr(ejercicio["inicial"], ejercicio)
    if inicial["sintaxis"]:
        problemas.append(f"el código inicial tiene error de sintaxis: {inicial['error']}")
    elif not inicial["error"] and inicial["pruebas"] and all(p["ok"] for p in inicial["pruebas"]):
        problemas.append("el código inicial ya pasa todas las pruebas")
    return problemas


def archivos_solucion_local(ejercicio_id: str) -> dict[str, str] | None:
    """Lee los bloques ```python archivo.py de la sección Solución de un ejercicio local."""
    numero, ejercicio = ejercicio_id[1:3], ejercicio_id.split("-e")[1]
    rutas = list((RAIZ / "contenido").glob(f"{numero}-*/e{ejercicio}.md"))
    if not rutas:
        return None
    texto = rutas[0].read_text(encoding="utf-8")
    solucion = re.split(r"^## Solución\s*$", texto, flags=re.M)[1].split("\n## Explicación")[0]
    archivos = {
        m.group(1): m.group(2)
        for m in re.finditer(r"^```[\w-]+[ \t]+([\w./-]+)[ \t]*\n(.*?)^```", solucion, re.S | re.M)
    }
    return archivos or None


def pytest_en(carpeta: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(carpeta), "-q", "-p", "no:cacheprovider", "--color=no"],
        cwd=carpeta, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def validar_local(ejercicio_id: str) -> list[str] | None:
    """Copia la carpeta del ejercicio, aplica la solución y corre pytest."""
    archivos = archivos_solucion_local(ejercicio_id)
    if archivos is None:
        return None
    origen = RAIZ / "ejercicios" / ejercicio_id
    problemas = []
    with tempfile.TemporaryDirectory(prefix="pydatos_local_") as temporal:
        # Se respeta la profundidad ejercicios/<id>/ para las pruebas que buscan la raíz del curso
        copia = Path(temporal) / "ejercicios" / ejercicio_id
        shutil.copytree(origen, copia, ignore=shutil.ignore_patterns("__pycache__"))
        inicial = pytest_en(copia)
        if inicial.returncode == 0:
            problemas.append("el código inicial ya pasa todas las pruebas")
        for nombre, contenido in archivos.items():
            destino = copia / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(contenido, encoding="utf-8")
        final = pytest_en(copia)
        if final.returncode != 0:
            ultimas = "\n         ".join(final.stdout.strip().splitlines()[-15:])
            problemas.append(f"la solución no pasa las pruebas:\n         {ultimas}")
    return problemas


def bloques_pyrun(texto: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"^```(?:pyrun|pytrace)\s*\n(.*?)^```", texto, re.S | re.M)]


def main() -> int:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    solo_retos = "--retos" in sys.argv
    filtro = argumentos[0] if argumentos else ""
    curso = json.loads((RAIZ / "contenido" / "curso.json").read_text(encoding="utf-8"))
    fallos = 0
    avisos = 0
    total = 0
    retos = 0
    retos_fallidos = 0
    for modulo in curso["modulos"]:
        if filtro and not modulo["id"].startswith(filtro):
            continue
        print(f"\n== Módulo {modulo['numero']}: {modulo['titulo']}")
        for leccion in modulo["lecciones"]:
            for i, bloque in enumerate([] if solo_retos else bloques_pyrun(leccion["contenido"]), 1):
                resultado = correr(bloque, {"archivos": ARCHIVOS_LECCION}, "ejecutar")
                if resultado["error"] and "# error esperado" not in bloque:
                    avisos += 1
                    print(f"  ⚠ {leccion['id']} bloque {i}: {resultado['error']}")
            for i, reto in enumerate(extraer_retos(leccion["contenido"], leccion["id"]), 1):
                retos += 1
                problemas = validar_ejercicio({**reto, "archivos": ARCHIVOS_LECCION})
                if problemas:
                    retos_fallidos += 1
                    print(f"  ❌ {leccion['id']}-r{i} · {reto['titulo']}")
                    for p in problemas:
                        print(f"       - {p}")
        for ejercicio in [] if solo_retos else modulo["ejercicios"]:
            if ejercicio["tipo"] == "web":
                problemas = validar_ejercicio(ejercicio)
            else:
                problemas = validar_local(ejercicio["id"])
                if problemas is None:
                    print(f"  ·  {ejercicio['id']} · {ejercicio['titulo']} (local, se revisa a mano)")
                    continue
            total += 1
            if problemas:
                fallos += 1
                print(f"  ❌ {ejercicio['id']} · {ejercicio['titulo']}")
                for p in problemas:
                    print(f"       - {p}")
            else:
                print(f"  ✅ {ejercicio['id']} · {ejercicio['titulo']}")
    print(f"\n{total - fallos}/{total} ejercicios correctos · {retos - retos_fallidos}/{retos} retos correctos · {avisos} avisos en lecciones")
    return 1 if fallos or retos_fallidos else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
