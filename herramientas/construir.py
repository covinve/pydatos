"""Construye contenido/curso.json a partir de los archivos Markdown del curso.

Uso (desde la carpeta del curso):
    python herramientas/construir.py

Estructura que lee:
    contenido/NN-nombre/modulo.md      datos del módulo
    contenido/NN-nombre/l1.md, l2.md   lecciones
    contenido/NN-nombre/e1.md, e2.md   ejercicios
    contenido/proyectos/p1.md          proyectos
    contenido/referencia/*.md          páginas de referencia
"""

from __future__ import annotations

import ast
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTENIDO = RAIZ / "contenido"
DATOS = CONTENIDO / "datos"

NIVELES = {"basico", "intermedio", "avanzado"}
DIFICULTADES = {"basico", "medio", "avanzado", "reto"}
TIPOS = {"web", "local"}
# Nombres que el evaluador agrega al espacio de las pruebas: el código del estudiante no debe usarlos
NOMBRES_DE_PRUEBAS = {"codigo", "salida", "igual", "cerca", "igual_df", "capturar", "lanza", "correr_pytest", "requiere"}


class ErrorContenido(Exception):
    pass


# ---------------------------------------------------------------------------
# Lectura de Markdown
# ---------------------------------------------------------------------------

def leer_frontmatter(texto: str, ruta: Path) -> tuple[dict, str]:
    """Separa el bloque `--- ... ---` inicial del resto del texto."""
    if not texto.startswith("---"):
        raise ErrorContenido(f"{ruta}: falta el encabezado ---")
    _, cabecera, cuerpo = texto.split("---", 2)
    datos: dict = {}
    clave_lista = None
    for linea in cabecera.strip().splitlines():
        if not linea.strip() or linea.strip().startswith("#"):
            continue
        if re.match(r"^\s+-\s", linea) and clave_lista:
            datos[clave_lista].append(linea.split("-", 1)[1].strip())
            continue
        if ":" not in linea:
            raise ErrorContenido(f"{ruta}: línea de encabezado inválida: {linea!r}")
        clave, valor = linea.split(":", 1)
        clave, valor = clave.strip(), valor.strip()
        if valor == "":
            datos[clave] = []
            clave_lista = clave
        else:
            clave_lista = None
            datos[clave] = int(valor) if re.fullmatch(r"-?\d+", valor) else valor
    return datos, cuerpo.lstrip("\n")


def secciones(cuerpo: str) -> list[tuple[str, str]]:
    """Divide el texto en secciones `## Título`, ignorando los bloques de código."""
    resultado: list[tuple[str, list[str]]] = [("", [])]
    en_codigo = False
    for linea in cuerpo.splitlines():
        if re.match(r"^\s*(```|~~~)", linea):
            en_codigo = not en_codigo
        encabezado = not en_codigo and re.match(r"^## (.+?)\s*$", linea)
        if encabezado:
            resultado.append((encabezado.group(1), []))
        else:
            resultado[-1][1].append(linea)
    return [(t, "\n".join(l).strip("\n")) for t, l in resultado]


def primer_bloque_codigo(texto: str, ruta: Path, seccion: str) -> str:
    coincidencia = re.search(r"^```[\w-]*[^\n]*\n(.*?)^```\s*$", texto, re.S | re.M)
    if not coincidencia:
        raise ErrorContenido(f"{ruta}: la sección «{seccion}» debe tener un bloque de código")
    return coincidencia.group(1).rstrip("\n") + "\n"


def leer_cuestionario(texto: str, ruta: Path) -> list[dict]:
    preguntas = []
    for bloque in re.split(r"\n\s*\n", texto.strip()):
        lineas = [l.rstrip() for l in bloque.strip().splitlines() if l.strip()]
        if not lineas:
            continue
        if not lineas[0].startswith("? "):
            raise ErrorContenido(f"{ruta}: cada pregunta debe empezar con '? ': {lineas[0]!r}")
        pregunta = {"pregunta": lineas[0][2:].strip(), "opciones": [], "correcta": None, "explicacion": ""}
        for linea in lineas[1:]:
            opcion = re.match(r"^- \[( |x)\] (.+)$", linea)
            if opcion:
                if opcion.group(1) == "x":
                    pregunta["correcta"] = len(pregunta["opciones"])
                pregunta["opciones"].append(opcion.group(2))
            elif linea.startswith("> "):
                pregunta["explicacion"] += (" " if pregunta["explicacion"] else "") + linea[2:].strip()
            else:
                raise ErrorContenido(f"{ruta}: línea no reconocida en el cuestionario: {linea!r}")
        if pregunta["correcta"] is None or len(pregunta["opciones"]) < 2:
            raise ErrorContenido(f"{ruta}: la pregunta «{pregunta['pregunta']}» necesita opciones y una marcada con [x]")
        preguntas.append(pregunta)
    return preguntas


def numero_archivo(ruta: Path) -> int:
    return int(re.search(r"\d+", ruta.stem).group())


def _armar_reto(titulo: str, cuerpo: str, ruta: Path | str) -> dict:
    nombre = f"{ruta}: reto «{titulo}»"
    if not titulo:
        raise ErrorContenido(f"{ruta}: cada :::reto necesita un título en la misma línea")
    bloques: dict[str, list[str]] = {}
    for m in re.finditer(r"^```(pyreto|pyprueba|pysolucion|pypreparacion)[ \t]*\n(.*?)^```[ \t]*$", cuerpo, re.S | re.M):
        bloques.setdefault(m.group(1), []).append(m.group(2).rstrip("\n") + "\n")
    for clase in ("pyreto", "pyprueba", "pysolucion"):
        if len(bloques.get(clase, [])) != 1:
            raise ErrorContenido(f"{nombre} debe tener exactamente un bloque ```{clase}")
    if len(bloques.get("pypreparacion", [])) > 1:
        raise ErrorContenido(f"{nombre} tiene más de un bloque ```pypreparacion")
    pista = re.search(r"^:::pista[^\n]*\n(.*?)^:::[ \t]*$", cuerpo, re.S | re.M)
    enunciado = re.sub(r"^```(pyreto|pyprueba|pysolucion|pypreparacion).*?^```[ \t]*$", "", cuerpo, flags=re.S | re.M)
    enunciado = re.sub(r"^:::pista.*?^:::[ \t]*$", "", enunciado, flags=re.S | re.M).strip()
    if not enunciado:
        raise ErrorContenido(f"{nombre} no tiene enunciado")
    if "def prueba_" not in bloques["pyprueba"][0]:
        raise ErrorContenido(f"{nombre}: el bloque ```pyprueba no tiene funciones prueba_*")
    try:
        arbol = ast.parse(bloques["pysolucion"][0])
    except SyntaxError as error:
        raise ErrorContenido(f"{nombre}: la solución tiene un error de sintaxis: {error}") from None
    definidos = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    definidos |= {n.name for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    choques = sorted(definidos & NOMBRES_DE_PRUEBAS)
    if choques:
        raise ErrorContenido(f"{nombre}: la solución usa {choques}, que las pruebas reservan para sí")
    return {
        "titulo": titulo,
        "enunciado": enunciado,
        "inicial": bloques["pyreto"][0],
        "pruebas": bloques["pyprueba"][0],
        "solucion": bloques["pysolucion"][0],
        "preparacion": bloques.get("pypreparacion", [""])[0],
        "pista": pista.group(1).strip() if pista else "",
    }


def extraer_retos(texto: str, ruta: Path | str = "") -> list[dict]:
    """Lee los bloques :::reto de una lección. También lo usa herramientas/validar.py.

    Formato (la pista y la preparación son opcionales):
        :::reto Título
        Enunciado en Markdown.
        ```pyreto        código inicial que ve el estudiante
        ```pyprueba      funciones prueba_* (ocultas)
        ```pysolucion    solución de referencia
        ```pypreparacion código oculto que corre antes (por ejemplo, borrar archivos de una ejecución anterior)
        :::pista
        Texto de la pista.
        :::
        :::
    """
    retos = []
    abiertos: list[str] = []
    reto = None
    en_codigo = False
    for linea in texto.splitlines():
        if re.match(r"^\s*(```|~~~)", linea):
            en_codigo = not en_codigo
        apertura = not en_codigo and re.match(r"^:::(\w+)\s*(.*)$", linea)
        cierre = not en_codigo and re.match(r"^:::\s*$", linea)
        if apertura:
            abiertos.append(apertura.group(1))
            if apertura.group(1) == "reto":
                if reto is not None:
                    raise ErrorContenido(f"{ruta}: hay un :::reto dentro de otro")
                reto = {"titulo": apertura.group(2).strip(), "lineas": [], "nivel": len(abiertos)}
                continue
        elif cierre and abiertos:
            if reto is not None and len(abiertos) == reto["nivel"]:
                retos.append(_armar_reto(reto["titulo"], "\n".join(reto["lineas"]), ruta))
                reto = None
                abiertos.pop()
                continue
            abiertos.pop()
        if reto is not None:
            reto["lineas"].append(linea)
    if reto is not None:
        raise ErrorContenido(f"{ruta}: al reto «{reto['titulo']}» le falta el ::: de cierre")
    return retos


# ---------------------------------------------------------------------------
# Elementos del curso
# ---------------------------------------------------------------------------

def leer_leccion(ruta: Path, modulo_id: str) -> dict:
    meta, cuerpo = leer_frontmatter(ruta.read_text(encoding="utf-8"), ruta)
    partes = re.split(r"^## Cuestionario\s*$", cuerpo, maxsplit=1, flags=re.M)
    contenido = partes[0].strip()
    quiz = leer_cuestionario(partes[1], ruta) if len(partes) > 1 else []
    for clave in ("titulo", "minutos"):
        if clave not in meta:
            raise ErrorContenido(f"{ruta}: falta «{clave}» en el encabezado")
    return {
        "id": f"{modulo_id}-l{numero_archivo(ruta)}",
        "titulo": meta["titulo"],
        "minutos": meta["minutos"],
        "resumen": meta.get("resumen", ""),
        "contenido": contenido,
        "retos": len(extraer_retos(contenido, ruta)),
        "quiz": quiz,
    }


def leer_ejercicio(ruta: Path, modulo_id: str) -> dict:
    meta, cuerpo = leer_frontmatter(ruta.read_text(encoding="utf-8"), ruta)
    ejercicio_id = f"{modulo_id}-e{numero_archivo(ruta)}"
    tipo = meta.get("tipo", "web")
    dificultad = meta.get("dificultad", "reto")
    if tipo not in TIPOS:
        raise ErrorContenido(f"{ruta}: tipo «{tipo}» inválido")
    if dificultad not in DIFICULTADES:
        raise ErrorContenido(f"{ruta}: dificultad «{dificultad}» inválida")
    partes = dict(secciones(cuerpo))
    for requerida in ("Enunciado", "Pista 1", "Pista 2", "Solución", "Explicación"):
        if requerida not in partes:
            raise ErrorContenido(f"{ruta}: falta la sección «## {requerida}»")
    ejercicio = {
        "id": ejercicio_id,
        "titulo": meta["titulo"],
        "dificultad": dificultad,
        "tipo": tipo,
        "tiempo": meta.get("tiempo", 20),
        "enunciado": partes["Enunciado"],
    }
    if tipo == "web":
        for requerida in ("Código inicial", "Pruebas"):
            if requerida not in partes:
                raise ErrorContenido(f"{ruta}: falta la sección «## {requerida}»")
        archivos = [a.strip() for a in str(meta.get("archivos", "")).split(",") if a.strip()]
        for archivo in archivos:
            if not (DATOS / archivo).exists():
                raise ErrorContenido(f"{ruta}: no existe el archivo de datos contenido/datos/{archivo}")
        pistas = [partes[t] for t in ("Pista 1", "Pista 2", "Pista 3") if t in partes]
        ejercicio.update(
            inicial=primer_bloque_codigo(partes["Código inicial"], ruta, "Código inicial"),
            pruebas=primer_bloque_codigo(partes["Pruebas"], ruta, "Pruebas"),
            preparacion=primer_bloque_codigo(partes["Preparación"], ruta, "Preparación") if "Preparación" in partes else "",
            pistas=pistas,
            solucion=primer_bloque_codigo(partes["Solución"], ruta, "Solución"),
            explicacion=partes["Explicación"],
            archivos=archivos,
            timeout=meta.get("timeout", 20),
        )
    else:
        carpeta = RAIZ / "ejercicios" / ejercicio_id
        if not carpeta.is_dir():
            raise ErrorContenido(f"{ruta}: falta la carpeta ejercicios/{ejercicio_id}/")
    return ejercicio


def leer_modulo(carpeta: Path) -> dict:
    ruta = carpeta / "modulo.md"
    meta, cuerpo = leer_frontmatter(ruta.read_text(encoding="utf-8"), ruta)
    numero = meta["numero"]
    modulo_id = f"m{numero:02d}"
    if meta.get("nivel") not in NIVELES:
        raise ErrorContenido(f"{ruta}: nivel inválido")
    lecciones = sorted(carpeta.glob("l[0-9]*.md"), key=numero_archivo)
    ejercicios = sorted(carpeta.glob("e[0-9]*.md"), key=numero_archivo)
    return {
        "id": modulo_id,
        "numero": numero,
        "nivel": meta["nivel"],
        "titulo": meta["titulo"],
        "resumen": meta.get("resumen", ""),
        "icono": meta.get("icono", "📘"),
        "objetivos": meta.get("objetivos", []),
        "introduccion": cuerpo.strip(),
        "lecciones": [leer_leccion(r, modulo_id) for r in lecciones],
        "ejercicios": [leer_ejercicio(r, modulo_id) for r in ejercicios],
    }


def leer_proyecto(ruta: Path) -> dict:
    meta, cuerpo = leer_frontmatter(ruta.read_text(encoding="utf-8"), ruta)
    partes = re.split(r"^## Criterios\s*$", cuerpo, maxsplit=1, flags=re.M)
    if len(partes) < 2:
        raise ErrorContenido(f"{ruta}: falta la sección «## Criterios»")
    criterios_texto, _, despues = partes[1].partition("\n## ")
    criterios = [re.sub(r"^- (\[ \] )?", "", l.strip()) for l in criterios_texto.strip().splitlines() if l.strip().startswith("- ")]
    contenido = partes[0].strip()
    if despues:
        contenido += "\n\n## " + despues.strip()
    return {
        "id": meta["id"],
        "nivel": meta["nivel"],
        "despues_de": meta["despues_de"],
        "titulo": meta["titulo"],
        "resumen": meta.get("resumen", ""),
        "carpeta": meta.get("carpeta", ""),
        "duracion": meta.get("duracion", ""),
        "contenido": contenido,
        "criterios": criterios,
    }


def leer_referencia(ruta: Path) -> dict:
    meta, cuerpo = leer_frontmatter(ruta.read_text(encoding="utf-8"), ruta)
    return {"id": ruta.stem, "titulo": meta["titulo"], "icono": meta.get("icono", "📄"), "orden": meta.get("orden", 99), "contenido": cuerpo.strip()}


def construir() -> dict:
    modulos = [leer_modulo(c) for c in sorted(CONTENIDO.glob("[0-9][0-9]-*")) if c.is_dir()]
    numeros = [m["numero"] for m in modulos]
    if len(numeros) != len(set(numeros)):
        raise ErrorContenido("Hay módulos con el mismo número")
    proyectos = [leer_proyecto(r) for r in sorted((CONTENIDO / "proyectos").glob("p*.md"))]
    referencias = sorted((leer_referencia(r) for r in (CONTENIDO / "referencia").glob("*.md")), key=lambda r: r["orden"])
    return {
        "titulo": "PyDatos",
        "generado": date.today().isoformat(),
        "modulos": modulos,
        "proyectos": proyectos,
        "referencias": referencias,
    }


def main() -> int:
    try:
        curso = construir()
    except ErrorContenido as error:
        print(f"❌ {error}")
        return 1
    destino = CONTENIDO / "curso.json"
    texto = json.dumps(curso, ensure_ascii=False, separators=(",", ":"))
    for intento in range(5):
        try:
            destino.write_text(texto, encoding="utf-8")
            break
        except OSError:
            # En Windows, el servidor local puede tener el archivo abierto un instante mientras lo envía
            if intento == 4:
                raise
            time.sleep(0.5)
    lecciones = sum(len(m["lecciones"]) for m in curso["modulos"])
    ejercicios = sum(len(m["ejercicios"]) for m in curso["modulos"])
    retos = sum(l["retos"] for m in curso["modulos"] for l in m["lecciones"])
    print(
        f"✅ curso.json: {len(curso['modulos'])} módulos, {lecciones} lecciones, {retos} retos, "
        f"{ejercicios} ejercicios, {len(curso['proyectos'])} proyectos ({destino.stat().st_size / 1024:.0f} KB)"
    )
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
