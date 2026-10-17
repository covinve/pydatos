"""Ejercicio m06-e4: resumir un archivo de CDR en ancho fijo de cualquier tamaño.

Uso:
    python ejercicios/m06-e4/ancho_fijo.py                                   # usa la muestra
    python ejercicios/m06-e4/ancho_fijo.py datos/1GB/cdr_ancho_fijo.txt      # archivo grande
"""

import sys
import time
from pathlib import Path

# (posición inicial, posición final) desde 1 e incluidas, según Referencia → Datos del curso
DISENO = {
    "cdr_id": (1, 12),
    "linea_origen": (13, 22),
    "tipo": (36, 40),
    "duracion_seg": (68, 73),
    "mb": (74, 83),
}


def resumir(ruta: Path) -> dict:
    """Recorre el archivo línea por línea y devuelve:

    - "registros": cantidad de registros
    - "por_tipo": diccionario tipo → cantidad (tipo sin espacios, tal como viene), ordenado por tipo
    - "minutos_voz": suma de minutos facturables de los registros VOZ con duración >= 0
    - "mb_datos": suma de las megas de los registros DATOS, redondeada a 3 decimales
    """
    # Escribe aquí tu solución
    raise NotImplementedError


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "muestra_ancho_fijo.txt"
    inicio = time.perf_counter()
    resultado = resumir(ruta)
    segundos = time.perf_counter() - inicio
    tamano_mb = ruta.stat().st_size / 1_000_000
    print(resultado)
    print(f"{tamano_mb:,.0f} MB procesados en {segundos:.1f} s ({tamano_mb / segundos:,.0f} MB/s)")
