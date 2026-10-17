"""Evaluador de código de PyDatos.

Este archivo se usa en dos lugares:
- En el navegador, dentro de Pyodide (assets/js/worker.js lo carga).
- En tu computador, desde herramientas/validar.py.

Ejecuta el código del estudiante, captura lo que imprime, corre las pruebas
de un ejercicio y, si se pide, registra paso a paso cómo cambian las variables.
"""

import base64
import contextlib
import io
import os
import sys
import traceback
import types

ARCHIVO_USUARIO = "<tu código>"
ARCHIVO_PRUEBAS = "<pruebas>"
MAX_SALIDA = 20_000
MAX_PASOS = 500

os.environ.setdefault("MPLBACKEND", "Agg")


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _recortar(texto, limite=MAX_SALIDA):
    if len(texto) <= limite:
        return texto
    return texto[:limite] + f"\n… (salida recortada: {len(texto) - limite} caracteres más)"


def _linea_usuario(exc):
    linea = None
    for marco in traceback.extract_tb(exc.__traceback__):
        if marco.filename == ARCHIVO_USUARIO:
            linea = marco.lineno
    return linea


def _mensaje_error(exc):
    texto = f"{type(exc).__name__}: {exc}"
    linea = _linea_usuario(exc)
    if linea:
        texto += f"  (línea {linea})"
    return texto


def _traceback_usuario(exc, codigo):
    """Traceback en español con solo las líneas del código del estudiante."""
    fuente = codigo.splitlines()
    cadena = []
    actual = exc
    while actual is not None and len(cadena) < 5:
        cadena.append(actual)
        if actual.__cause__ is not None:
            actual = actual.__cause__
        elif actual.__context__ is not None and not actual.__suppress_context__:
            actual = actual.__context__
        else:
            actual = None
    textos = []
    for posicion, error in enumerate(reversed(cadena)):
        if posicion:
            textos.append("")
            textos.append("La excepción anterior provocó esta otra:")
            textos.append("")
        textos.append("Traceback (la llamada más reciente va al final):")
        for marco in traceback.extract_tb(error.__traceback__):
            if marco.filename != ARCHIVO_USUARIO:
                continue
            nombre = "programa principal" if marco.name == "<module>" else f"{marco.name}()"
            textos.append(f"  Línea {marco.lineno}, en {nombre}")
            if 0 < marco.lineno <= len(fuente):
                textos.append("    " + fuente[marco.lineno - 1].strip())
        textos.append(f"{type(error).__name__}: {error}")
    return "\n".join(textos)


def _repr_corto(valor, limite=70):
    try:
        texto = repr(valor)
    except Exception:  # pragma: no cover - objetos con repr roto
        texto = "<?>"
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def _figuras():
    """Convierte las figuras abiertas de matplotlib en PNG (base64)."""
    if "matplotlib.pyplot" not in sys.modules:
        return []
    plt = sys.modules["matplotlib.pyplot"]
    imagenes = []
    for numero in plt.get_fignums():
        figura = plt.figure(numero)
        buffer = io.BytesIO()
        figura.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
        imagenes.append(base64.b64encode(buffer.getvalue()).decode("ascii"))
    plt.close("all")
    return imagenes


@contextlib.contextmanager
def _modulo_principal():
    """Crea un módulo limpio que hace de __main__ mientras corre el código."""
    modulo = types.ModuleType("__main__")
    modulo.__dict__["__builtins__"] = __builtins__
    anterior = sys.modules.get("__main__")
    sys.modules["__main__"] = modulo
    try:
        yield modulo.__dict__
    finally:
        if anterior is not None:
            sys.modules["__main__"] = anterior


# ---------------------------------------------------------------------------
# Ayudas disponibles dentro de las pruebas
# ---------------------------------------------------------------------------

def _son_iguales(a, b):
    try:
        resultado = a == b
        if isinstance(resultado, bool):
            return resultado
        import numpy as np  # noqa: PLC0415

        if np.ndim(resultado) == 0:
            return bool(resultado)
        return bool(np.all(resultado)) and np.shape(a) == np.shape(b)
    except Exception:
        return False


def igual(obtenido, esperado, mensaje=""):
    """Falla si `obtenido` es distinto de `esperado` y muestra ambos valores."""
    if not _son_iguales(obtenido, esperado):
        detalle = f"se esperaba {esperado!r}, pero se obtuvo {obtenido!r}"
        raise AssertionError(f"{mensaje} — {detalle}" if mensaje else detalle)


def cerca(obtenido, esperado, tolerancia=1e-6, mensaje=""):
    """Compara números con tolerancia (para resultados con decimales)."""
    try:
        ok = abs(obtenido - esperado) <= tolerancia
    except TypeError:
        ok = False
    if not ok:
        detalle = f"se esperaba ≈{esperado!r} (±{tolerancia}), pero se obtuvo {obtenido!r}"
        raise AssertionError(f"{mensaje} — {detalle}" if mensaje else detalle)


def igual_df(obtenido, esperado, mensaje="", **opciones):
    """Compara dos DataFrames de pandas sin exigir el mismo tipo de dato."""
    import pandas as pd  # noqa: PLC0415

    if not isinstance(obtenido, pd.DataFrame):
        raise AssertionError(f"{mensaje} — se esperaba un DataFrame y se obtuvo {type(obtenido).__name__}")
    opciones.setdefault("check_dtype", False)
    try:
        pd.testing.assert_frame_equal(
            obtenido.reset_index(drop=True), esperado.reset_index(drop=True), **opciones
        )
    except AssertionError as exc:
        primera = str(exc).strip().splitlines()[0]
        raise AssertionError(f"{mensaje} — {primera}" if mensaje else primera) from None


def capturar(funcion, *args, **kwargs):
    """Ejecuta `funcion` y devuelve (resultado, texto_impreso)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        resultado = funcion(*args, **kwargs)
    return resultado, buffer.getvalue()


def lanza(tipo_excepcion, funcion, *args, **kwargs):
    """Falla si `funcion(*args)` NO lanza la excepción indicada. Devuelve la excepción."""
    try:
        funcion(*args, **kwargs)
    except tipo_excepcion as exc:
        return exc
    except Exception as exc:
        raise AssertionError(
            f"se esperaba {tipo_excepcion.__name__}, pero se lanzó {type(exc).__name__}: {exc}"
        ) from None
    raise AssertionError(f"se esperaba que lanzara {tipo_excepcion.__name__}, pero no lanzó nada")


def correr_pytest(codigo_pruebas, modulos, archivo_pruebas="test_alumno.py"):
    """Escribe `modulos` ({nombre: código}) y las pruebas en disco y ejecuta pytest.

    Devuelve (código_de_salida, texto). Código 0: todas pasan; 1: alguna falla; 5: no hay pruebas.
    Se usa para comprobar que las pruebas del estudiante detectan versiones con errores.
    """
    import importlib
    import pathlib
    import shutil

    import pytest

    sys.dont_write_bytecode = True
    for nombre, fuente in modulos.items():
        pathlib.Path(f"{nombre}.py").write_text(fuente, encoding="utf-8")
    pathlib.Path(archivo_pruebas).write_text(codigo_pruebas, encoding="utf-8")
    shutil.rmtree("__pycache__", ignore_errors=True)
    importlib.invalidate_caches()
    for nombre in [*modulos, archivo_pruebas.removesuffix(".py"), "conftest"]:
        sys.modules.pop(nombre, None)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        codigo_salida = pytest.main(["-q", "-p", "no:cacheprovider", "--no-header", "-o", "console_output_style=classic", archivo_pruebas])
    return int(codigo_salida), buffer.getvalue()


def _crear_requiere(espacio):
    def requiere(*nombres):
        """Comprueba que el estudiante definió estos nombres."""
        faltan = [n for n in nombres if n not in espacio]
        if faltan:
            lista = ", ".join(f"`{n}`" for n in faltan)
            raise AssertionError(f"Debes definir {lista} en tu código")

    return requiere


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------

_CARPETAS_DE_TRABAJO = set()


def _limpiar_modulos_locales():
    """Permite importar módulos de la carpeta de trabajo y olvida los de ejecuciones anteriores
    (de esta carpeta o de carpetas de trabajo usadas antes, como hace el validador)."""
    import importlib

    carpeta = os.getcwd()
    _CARPETAS_DE_TRABAJO.add(carpeta)
    for vieja in _CARPETAS_DE_TRABAJO - {carpeta}:
        while vieja in sys.path:
            sys.path.remove(vieja)
    if carpeta not in sys.path:
        sys.path.insert(0, carpeta)
    prefijos = tuple(c + os.sep for c in _CARPETAS_DE_TRABAJO)
    for nombre, modulo in list(sys.modules.items()):
        archivo = getattr(modulo, "__file__", None) or ""
        if archivo and os.path.abspath(archivo).startswith(prefijos):
            del sys.modules[nombre]
    importlib.invalidate_caches()


def _preparar(preparacion):
    _limpiar_modulos_locales()
    if preparacion and preparacion.strip():
        espacio = {"__name__": "preparacion"}
        exec(compile(preparacion, "<preparación>", "exec"), espacio)


def ejecutar(codigo, modo="ejecutar", pruebas="", preparacion=""):
    """Ejecuta el código del estudiante.

    modo = "ejecutar": solo corre el código y devuelve lo que imprime.
    modo = "probar":   además corre las funciones prueba_* de `pruebas`.
    """
    resultado = {
        "salida": "",
        "error": None,
        "sintaxis": False,
        "pruebas": [],
        "figuras": [],
    }
    try:
        _preparar(preparacion)
    except Exception as exc:  # error del curso, no del estudiante
        resultado["error"] = f"Error preparando el ejercicio: {_mensaje_error(exc)}"
        return resultado

    try:
        compilado = compile(codigo, ARCHIVO_USUARIO, "exec")
    except SyntaxError as exc:
        resultado["sintaxis"] = True
        resultado["error"] = f"{type(exc).__name__}: {exc.msg} (línea {exc.lineno})"
        return resultado

    buffer = io.StringIO()
    with _modulo_principal() as espacio:
        try:
            with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                exec(compilado, espacio)
        except SystemExit:
            pass
        except BaseException as exc:  # noqa: BLE001 - mostramos cualquier error al estudiante
            resultado["error"] = _traceback_usuario(exc, codigo)
        resultado["salida"] = _recortar(buffer.getvalue())
        resultado["figuras"] = _figuras()

        if modo == "probar" and resultado["error"] is None:
            resultado["pruebas"] = _correr_pruebas(espacio, pruebas, codigo, resultado["salida"])
    return resultado


def _correr_pruebas(espacio, pruebas, codigo, salida):
    espacio_pruebas = dict(espacio)
    espacio_pruebas.update(
        igual=igual,
        cerca=cerca,
        igual_df=igual_df,
        capturar=capturar,
        lanza=lanza,
        correr_pytest=correr_pytest,
        requiere=_crear_requiere(espacio),
        codigo=codigo,
        salida=salida,
    )
    antes = set(espacio_pruebas)
    try:
        exec(compile(pruebas, ARCHIVO_PRUEBAS, "exec"), espacio_pruebas)
    except Exception as exc:
        return [{"nombre": "Preparar las pruebas", "ok": False, "mensaje": _mensaje_error(exc)}]

    informes = []
    for nombre, funcion in list(espacio_pruebas.items()):
        if nombre in antes or not nombre.startswith("prueba_") or not callable(funcion):
            continue
        descripcion = (funcion.__doc__ or nombre.removeprefix("prueba_").replace("_", " ")).strip()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                funcion()
            informes.append({"nombre": descripcion, "ok": True, "mensaje": ""})
        except AssertionError as exc:
            mensaje = str(exc).strip() or "El resultado no es el esperado"
            informes.append({"nombre": descripcion, "ok": False, "mensaje": mensaje})
        except BaseException as exc:  # noqa: BLE001
            informes.append({"nombre": descripcion, "ok": False, "mensaje": _mensaje_error(exc)})
        _figuras()  # descarta figuras creadas durante las pruebas
    return informes


# ---------------------------------------------------------------------------
# Visualizador paso a paso
# ---------------------------------------------------------------------------

class _LimitePasos(Exception):
    pass


def _variables(diccionario):
    variables = {}
    for nombre, valor in diccionario.items():
        if nombre.startswith("__") or isinstance(valor, types.ModuleType):
            continue
        if isinstance(valor, types.FunctionType):
            variables[nombre] = f"<función {valor.__name__}>"
        elif isinstance(valor, type):
            variables[nombre] = f"<clase {valor.__name__}>"
        else:
            variables[nombre] = _repr_corto(valor)
    return variables


def trazar(codigo):
    """Ejecuta el código registrando cada línea y el valor de las variables."""
    resultado = {"pasos": [], "error": None, "sintaxis": False, "limite": False}
    try:
        compilado = compile(codigo, ARCHIVO_USUARIO, "exec")
    except SyntaxError as exc:
        resultado["sintaxis"] = True
        resultado["error"] = f"{type(exc).__name__}: {exc.msg} (línea {exc.lineno})"
        return resultado

    pasos = resultado["pasos"]
    buffer = io.StringIO()

    def pila(marco):
        nombres = []
        while marco is not None and marco.f_code.co_filename == ARCHIVO_USUARIO:
            nombre = marco.f_code.co_name
            nombres.append("programa" if nombre == "<module>" else nombre)
            marco = marco.f_back
        return list(reversed(nombres))

    def rastreador(marco, evento, argumento):
        if marco.f_code.co_filename != ARCHIVO_USUARIO:
            return None
        if marco.f_code.co_name in ("<listcomp>", "<genexpr>", "<dictcomp>", "<setcomp>"):
            return rastreador
        if evento in ("line", "return"):
            if len(pasos) >= MAX_PASOS:
                raise _LimitePasos
            en_funcion = marco.f_code.co_name != "<module>"
            pasos.append(
                {
                    "linea": marco.f_lineno,
                    "evento": evento,
                    "pila": pila(marco),
                    "locales": _variables(marco.f_locals) if en_funcion else {},
                    "globales": _variables(marco.f_globals),
                    "salida": _recortar(buffer.getvalue(), 4000),
                    "retorno": _repr_corto(argumento) if evento == "return" and en_funcion else None,
                }
            )
        return rastreador

    with _modulo_principal() as espacio:
        try:
            with contextlib.redirect_stdout(buffer):
                sys.settrace(rastreador)
                try:
                    exec(compilado, espacio)
                finally:
                    sys.settrace(None)
        except _LimitePasos:
            resultado["limite"] = True
        except BaseException as exc:  # noqa: BLE001
            resultado["error"] = _mensaje_error(exc)
    resultado["salida_final"] = _recortar(buffer.getvalue(), 4000)
    _figuras()
    return resultado
