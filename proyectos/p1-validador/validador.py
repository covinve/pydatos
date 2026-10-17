"""Proyecto 1 · Validador de archivos de facturación.

Uso:
    python proyectos/p1-validador/validador.py --cdr datos/10MB/cdr.csv --clientes datos/10MB/clientes.csv --salida reportes/10MB

Lee la guía completa en la página del curso: Nivel básico → Proyecto 1.
Las funciones de abajo son el "contrato" que revisan las pruebas de tests/test_validador.py.
Puedes (y deberías) agregar todas las funciones auxiliares que necesites.
"""

from __future__ import annotations

from pathlib import Path

TIPOS_VALIDOS = {"VOZ", "SMS", "DATOS"}
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"
ERRORES = ["duplicado", "linea_vacia", "linea_desconocida", "tipo_desconocido", "duracion_negativa", "fecha_invalida"]


def cargar_lineas_clientes(ruta_clientes: Path) -> set[str]:
    """Devuelve el conjunto de líneas de clientes.csv (archivo en latin-1)."""
    raise NotImplementedError


def clasificar(fila: dict[str, str], vistos: set[str], lineas_clientes: set[str]) -> str | None:
    """Devuelve el nombre del primer error del CDR (en el orden de ERRORES) o None si es válido.

    `vistos` es el conjunto de cdr_id ya leídos: esta función debe agregar el cdr_id de la fila.
    """
    raise NotImplementedError


def validar_archivo(ruta_cdr: Path, ruta_clientes: Path, carpeta_salida: Path) -> dict:
    """Valida el archivo completo recorriéndolo línea por línea.

    Escribe en carpeta_salida:
      - rechazados.csv: los CDR inválidos con todas sus columnas más "motivo" (separado por |, UTF-8).
      - resumen.json: el diccionario que devuelve esta función.

    Devuelve un diccionario con las mismas claves que la sección "cdr" de esperado.json:
    registros_totales, registros_validos, errores, validos_por_tipo, minutos_nacionales,
    minutos_internacionales, mb_totales, sms_totales y lineas_con_consumo.
    """
    raise NotImplementedError


def comparar_con_esperado(resumen: dict, ruta_esperado: Path) -> list[str]:
    """Compara el resumen con la sección "cdr" de esperado.json.

    Devuelve una lista de textos, uno por cada diferencia, por ejemplo:
    "minutos_nacionales: obtenido 2350, esperado 2358". Lista vacía = todo cuadra.
    Solo compara las claves que existen en el resumen.
    """
    raise NotImplementedError


def main() -> None:
    """Lee los argumentos de la terminal, valida, compara (si hay esperado.json) y muestra el reporte."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
