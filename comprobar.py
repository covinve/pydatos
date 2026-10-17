"""Comprueba tus ejercicios de VS Code.

Uso (desde la carpeta del curso, con el entorno virtual activo):
    python comprobar.py m06-e3          comprueba el ejercicio m06-e3
    python comprobar.py m06-e3 --pista  vuelve a mostrar las pistas que ya desbloqueaste
    python comprobar.py --lista         muestra el estado de todos tus ejercicios locales
    python comprobar.py m06-e3 --reiniciar   vuelve a empezar el ejercicio (para repasarlo)

Funciona igual que los ejercicios de la página:
  - cada vez que fallan las pruebas gastas un intento y se desbloquea una pista;
  - al tercer fallo se muestra la solución explicada;
  - los errores de sintaxis NO gastan intento.

Tus intentos se guardan en .progreso/intentos.json (súbelo a Git para tenerlos en casa y en la oficina).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ARCHIVO_INTENTOS = RAIZ / ".progreso" / "intentos.json"
MAX_INTENTOS = 3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VERDE, ROJO, AMARILLO, AZUL, GRIS, NEGRITA, FIN = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[90m", "\033[1m", "\033[0m"


def color(texto: str, codigo: str) -> str:
    return f"{codigo}{texto}{FIN}" if sys.stdout.isatty() else texto


# ---------------------------------------------------------------------------
# Lectura de los ejercicios
# ---------------------------------------------------------------------------

def buscar_ejercicio(ejercicio_id: str) -> Path | None:
    coincidencia = re.fullmatch(r"m(\d{2})-e(\d+)", ejercicio_id)
    if not coincidencia:
        return None
    numero, ejercicio = int(coincidencia.group(1)), coincidencia.group(2)
    for carpeta in (RAIZ / "contenido").glob(f"{numero:02d}-*"):
        archivo = carpeta / f"e{ejercicio}.md"
        if archivo.exists():
            return archivo
    return None


def leer_secciones(ruta: Path) -> tuple[dict, dict]:
    texto = ruta.read_text(encoding="utf-8")
    _, cabecera, cuerpo = texto.split("---", 2)
    meta = {}
    for linea in cabecera.strip().splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            meta[clave.strip()] = valor.strip()
    partes: dict[str, list[str]] = {}
    actual = None
    en_codigo = False
    for linea in cuerpo.splitlines():
        if re.match(r"^\s*(```|~~~)", linea):
            en_codigo = not en_codigo
        encabezado = not en_codigo and re.match(r"^## (.+?)\s*$", linea)
        if encabezado:
            actual = encabezado.group(1)
            partes[actual] = []
        elif actual:
            partes[actual].append(linea)
    return meta, {k: "\n".join(v).strip() for k, v in partes.items()}


def ejercicios_locales() -> list[str]:
    ids = []
    for archivo in sorted((RAIZ / "contenido").glob("[0-9][0-9]-*/e*.md")):
        texto = archivo.read_text(encoding="utf-8")
        if re.search(r"^tipo:\s*local\s*$", texto, re.M):
            numero = int(archivo.parent.name[:2])
            ids.append(f"m{numero:02d}-{archivo.stem}")
    return sorted(ids, key=lambda i: (int(i[1:3]), int(i.split("-e")[1])))


# ---------------------------------------------------------------------------
# Intentos
# ---------------------------------------------------------------------------

def cargar_intentos() -> dict:
    if ARCHIVO_INTENTOS.exists():
        return json.loads(ARCHIVO_INTENTOS.read_text(encoding="utf-8"))
    return {}


def guardar_intentos(datos: dict) -> None:
    ARCHIVO_INTENTOS.parent.mkdir(exist_ok=True)
    ARCHIVO_INTENTOS.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Pantalla
# ---------------------------------------------------------------------------

def mostrar_markdown(titulo: str, texto: str, codigo_color: str = AZUL) -> None:
    print()
    print(color(f"━━━ {titulo} " + "━" * max(3, 60 - len(titulo)), codigo_color))
    for linea in texto.splitlines():
        if linea.startswith("```"):
            print(color("    " + "─" * 40, GRIS))
        else:
            print("    " + linea)
    print()


def mostrar_ayudas(meta: dict, partes: dict, intentos: int, resuelto: bool) -> None:
    for i in (1, 2, 3):
        clave = f"Pista {i}"
        if clave in partes and (intentos >= i or resuelto):
            mostrar_markdown(f"💡 {clave}", partes[clave], AMARILLO)
    if intentos >= MAX_INTENTOS or resuelto:
        mostrar_markdown("📘 Solución", partes.get("Solución", "(sin solución)"), VERDE)
        mostrar_markdown("📖 Explicación", partes.get("Explicación", ""), VERDE)


def resumen_pytest(salida: str) -> str:
    lineas = [l for l in salida.splitlines() if l.strip()]
    utiles = [l for l in lineas if re.search(r"(FAILED|PASSED|ERROR|AssertionError|assert |Error:|^E\s)", l)]
    return "\n".join(utiles[-40:]) if utiles else "\n".join(lineas[-25:])


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------

def comprobar(ejercicio_id: str) -> int:
    ruta = buscar_ejercicio(ejercicio_id)
    if not ruta:
        print(color(f"No existe el ejercicio «{ejercicio_id}». Usa el formato m06-e3 (módulo 6, ejercicio 3).", ROJO))
        return 2
    meta, partes = leer_secciones(ruta)
    carpeta = RAIZ / "ejercicios" / ejercicio_id
    if meta.get("tipo") != "local" or not carpeta.is_dir():
        print(color("Este ejercicio se resuelve en la página web, no en VS Code.", AMARILLO))
        return 2

    datos = cargar_intentos()
    estado = datos.get(ejercicio_id, {"intentos": 0, "estado": "nuevo"})
    print(color(f"\n🧪 Comprobando {ejercicio_id} · {meta.get('titulo', '')}", NEGRITA))
    try:
        import pytest  # noqa: F401
    except ImportError:
        print(color("No está instalado pytest. Activa tu entorno virtual y ejecuta: pip install -r requirements.txt", ROJO))
        return 2

    proceso = subprocess.run(
        [sys.executable, "-m", "pytest", str(carpeta), "-q", "--tb=short", "-p", "no:cacheprovider", "--color=no"],
        cwd=carpeta,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    salida = proceso.stdout + proceso.stderr

    if proceso.returncode == 0:
        anterior = estado.get("estado")
        estado.update(estado="resuelto", fecha=date.today().isoformat())
        datos[ejercicio_id] = estado
        guardar_intentos(datos)
        aprobadas = re.search(r"(\d+) passed", salida)
        print(color(f"\n🎉 ¡Todas las pruebas pasaron! ({aprobadas.group(1) if aprobadas else '?'} pruebas)", VERDE))
        if anterior == "solucion":
            print("   Lo resolviste en tu repaso: ya no depende de la solución.")
        print("   Marca el ejercicio como ✅ resuelto en la página del curso.")
        mostrar_ayudas(meta, partes, estado.get("intentos", 0), resuelto=True)
        return 0

    sintaxis = proceso.returncode in (2, 4) and re.search(r"(SyntaxError|IndentationError)", salida)
    if sintaxis or proceso.returncode == 5:
        motivo = "un error de sintaxis" if sintaxis else "no se encontraron pruebas"
        print(color(f"\n✏️  Hay {motivo}. No cuenta como intento.", AMARILLO))
        print(resumen_pytest(salida))
        return 1

    intentos = estado.get("intentos", 0) + 1
    estado["intentos"] = intentos
    if intentos >= MAX_INTENTOS and estado.get("estado") != "resuelto":
        estado["estado"] = "solucion"
    elif estado.get("estado") == "nuevo":
        estado["estado"] = "en_curso"
    datos[ejercicio_id] = estado
    guardar_intentos(datos)

    fallidas = re.search(r"(\d+) failed", salida)
    aprobadas = re.search(r"(\d+) passed", salida)
    print(color(f"\n❌ {fallidas.group(1) if fallidas else 'Algunas'} pruebas fallaron"
                f"{f', {aprobadas.group(1)} pasaron' if aprobadas else ''}.", ROJO))
    print(color("─" * 64, GRIS))
    print(resumen_pytest(salida))
    print(color("─" * 64, GRIS))
    restantes = MAX_INTENTOS - intentos
    if estado.get("estado") == "resuelto":
        print("Ya lo habías resuelto antes; esta versión no pasa todas las pruebas.")
    elif restantes > 0:
        print(color(f"Intento {intentos} de {MAX_INTENTOS}. Te quedan {restantes} antes de ver la solución.", AMARILLO))
    else:
        print(color("Se desbloqueó la solución explicada. Revísala y sigue adelante.", AMARILLO))
        print("Marca el ejercicio como 📖 'resuelto viendo la solución' en la página para repasarlo después.")
    mostrar_ayudas(meta, partes, intentos, resuelto=False)
    return 1


def pistas(ejercicio_id: str) -> int:
    ruta = buscar_ejercicio(ejercicio_id)
    if not ruta:
        print(color(f"No existe el ejercicio «{ejercicio_id}».", ROJO))
        return 2
    meta, partes = leer_secciones(ruta)
    estado = cargar_intentos().get(ejercicio_id, {"intentos": 0})
    if not estado.get("intentos") and estado.get("estado") != "resuelto":
        print("Todavía no has desbloqueado pistas: se desbloquean al fallar las pruebas.")
        return 0
    mostrar_ayudas(meta, partes, estado.get("intentos", 0), estado.get("estado") == "resuelto")
    return 0


def reiniciar(ejercicio_id: str) -> int:
    datos = cargar_intentos()
    if ejercicio_id in datos:
        datos[ejercicio_id]["intentos"] = 0
        guardar_intentos(datos)
    print(f"Listo: {ejercicio_id} vuelve a empezar sin pistas. Tu código no se borró.")
    return 0


def lista() -> int:
    datos = cargar_intentos()
    simbolos = {"nuevo": "○", "en_curso": "◐", "solucion": "📖", "resuelto": "✅"}
    print(color("\nEjercicios para resolver en VS Code\n", NEGRITA))
    for ejercicio_id in ejercicios_locales():
        ruta = buscar_ejercicio(ejercicio_id)
        meta, _ = leer_secciones(ruta)
        estado = datos.get(ejercicio_id, {"estado": "nuevo", "intentos": 0})
        intentos = f"{estado.get('intentos', 0)} intentos" if estado.get("intentos") else ""
        print(f"  {simbolos.get(estado['estado'], '○')}  {ejercicio_id:<8} {meta.get('titulo', ''):<55} {color(intentos, GRIS)}")
    print()
    return 0


def main(argumentos: list[str]) -> int:
    if not argumentos or argumentos[0] in ("-h", "--help", "ayuda"):
        print(__doc__)
        return 0
    if argumentos[0] == "--lista":
        return lista()
    ejercicio_id = argumentos[0].lower()
    if "--pista" in argumentos or "--pistas" in argumentos:
        return pistas(ejercicio_id)
    if "--reiniciar" in argumentos:
        return reiniciar(ejercicio_id)
    return comprobar(ejercicio_id)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
