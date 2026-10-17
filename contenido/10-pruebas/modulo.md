---
numero: 10
nivel: intermedio
titulo: Pruebas automáticas con pytest
icono: 🧪
resumen: Escribir pruebas que atrapan errores antes que tus usuarios, con pytest, fixtures, parametrización, cobertura y desarrollo guiado por pruebas.
objetivos:
  - Escribir y ejecutar pruebas con **pytest** e interpretar sus fallos.
  - Reutilizar preparación con **fixtures** y probar muchos casos con **parametrize**.
  - Elegir **qué** probar: casos borde, clases de equivalencia y pruebas de regresión.
  - Probar código que usa archivos, variables de entorno, la salida en pantalla y el logging.
  - Medir la **cobertura** y entender sus límites.
  - Practicar el ciclo **TDD**: rojo, verde, refactorizar.
---

En este módulo los papeles se invierten: **tú escribes las pruebas** y el curso comprueba que tus pruebas sean buenas, ejecutándolas contra versiones del código con errores sembrados a propósito (*mutantes*). Una buena batería de pruebas debe pasar con el código correcto y **fallar** con cada mutante.
