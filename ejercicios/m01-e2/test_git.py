"""Pruebas del ejercicio m01-e2: tu primer commit."""

import shutil
import subprocess
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "presentacion.md"


def git(*argumentos):
    proceso = subprocess.run(["git", *argumentos], cwd=CARPETA, capture_output=True, text=True, encoding="utf-8")
    return proceso.returncode, proceso.stdout.strip()


def test_git_instalado():
    assert shutil.which("git"), "No se encontró Git. Instálalo desde git-scm.com"


def test_git_configurado():
    _, nombre = git("config", "user.name")
    _, correo = git("config", "user.email")
    assert nombre, 'Falta configurar tu nombre: git config --global user.name "Tu Nombre"'
    assert "@" in correo, 'Falta configurar tu correo: git config --global user.email "tu@correo.com"'


def test_el_curso_es_un_repositorio():
    codigo, _ = git("rev-parse", "--is-inside-work-tree")
    assert codigo == 0, "La carpeta del curso no es un repositorio de Git. Revisa la lección 3 (git init / git clone)."


def test_presentacion_con_contenido():
    assert ARCHIVO.exists(), "No existe ejercicios/m01-e2/presentacion.md"
    lineas = [l.strip() for l in ARCHIVO.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert any(l.startswith("# ") for l in lineas), "La presentación necesita un título que empiece con '# '"
    objetivos = [l for l in lineas if l.startswith(("- ", "* "))]
    assert len(objetivos) >= 3, f"Escribe al menos 3 objetivos como lista (con '- '); encontré {len(objetivos)}"


def test_presentacion_guardada_en_un_commit():
    codigo, historia = git("log", "--oneline", "--", "presentacion.md")
    assert codigo == 0 and historia, "presentacion.md no está en ningún commit todavía: haz git add y git commit"
    _, pendientes = git("status", "--porcelain", "--", "presentacion.md")
    assert not pendientes, "presentacion.md tiene cambios sin guardar: haz git add y git commit de nuevo"
