"""Facturación organizada en capas (ejercicio m19-e7).

dominio.py          reglas de negocio puras (solo biblioteca estándar: dataclasses, datetime, math, typing...)
puertos.py          contratos (Protocol) que necesita el servicio
adaptadores_csv.py  lectura y escritura de CSV (implementan los puertos)
servicios.py        el caso de uso "facturar" (solo conoce dominio y puertos)
cli.py              raíz de composición: crea los adaptadores y llama al servicio
"""
