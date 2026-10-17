"""Tus pruebas de integración del adaptador ClientesSQLite (ejercicio m20-e8).

Prueba contra SQLite DE VERDAD (un archivo en tmp_path), usando los fixtures de conftest.py.
"""

from datetime import date

import pytest

from repositorio_sqlite import Cliente, ClienteNoEncontrado, ClientesSQLite, cargar_csv


# Escribe aquí tus pruebas
