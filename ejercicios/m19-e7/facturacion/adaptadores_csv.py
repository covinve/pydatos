"""Adaptadores CSV.

    FuenteCSV(carpeta)  implementa FuenteDatos con planes.csv, clientes.csv (latin-1) y cdr.csv (separador |).
                        cdrs() es un generador de diccionarios (como csv.DictReader).
    SalidaCSV(ruta)     implementa SalidaFacturas: escribe el CSV con las mismas columnas y formato que monolito.py
                        (crea la carpeta si no existe).
"""
