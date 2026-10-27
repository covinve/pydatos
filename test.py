import sys

print("Versión:", sys.version.split()[0])
print("Ejecutable:", sys.executable)
en_venv = sys.prefix != sys.base_prefix
print("¿Dentro de un entorno virtual?", en_venv)
