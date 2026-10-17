"""Adaptadores de la conciliación.

    EmitidasCSV(ruta)   implementa FacturasEmitidas leyendo facturas.csv (utf-8; la línea como texto).
    ReporteJSON(ruta)   implementa SalidaConciliacion: escribe {"resumen": {...}, "hallazgos": [{...}, ...]}
                        (utf-8, ensure_ascii=False, indent=2), creando la carpeta si no existe.
"""
