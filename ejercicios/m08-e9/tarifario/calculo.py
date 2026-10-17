"""Cálculo de valores con el tarifario incluido en el paquete."""


def cargar_tarifas() -> dict[str, int]:
    """Lee tarifario/datos/tarifas.json desde DENTRO del paquete (sin depender de la carpeta actual)
    y devuelve el diccionario de tarifas."""
    raise NotImplementedError


def valor(destino: str, segundos: int) -> int:
    """Minutos facturables × tarifa del destino. Lanza KeyError si el destino no existe."""
    raise NotImplementedError
