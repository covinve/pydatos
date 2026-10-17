---
numero: 16
nivel: avanzado
titulo: Datos grandes con DuckDB y Polars
icono: 🚀
resumen: Motores columnares que procesan 20 GB en tu computador de 16 GB. SQL sobre archivos con DuckDB, expresiones perezosas con Polars, procesamiento en paralelo y cómo medir para elegir la herramienta correcta.
objetivos:
  - Entender por qué los motores columnares superan a Pandas con archivos grandes.
  - Consultar CSV y Parquet con **SQL** usando DuckDB, sin cargarlos en memoria.
  - Escribir consultas con **funciones de ventana** (duplicados, rankings, acumulados).
  - Usar **Polars** con expresiones y evaluación perezosa (`scan_csv`, `collect`).
  - Paralelizar trabajo independiente con `concurrent.futures`.
  - **Medir** tiempo y memoria para elegir la herramienta adecuada.
---
