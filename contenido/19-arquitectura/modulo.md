---
numero: 19
nivel: avanzado
titulo: Arquitectura en capas
icono: 🏛️
resumen: Cómo organizar un programa que crece sin que se vuelva un enredo. Dominio, casos de uso e infraestructura; objetos de valor; puertos con Protocol; el patrón repositorio; inyección de dependencias y los principios SOLID aplicados a facturación.
objetivos:
  - Separar las **reglas de negocio** (dominio) de la lectura y escritura (infraestructura).
  - Modelar conceptos del negocio con **objetos de valor** inmutables (`dataclass(frozen=True)`).
  - Definir **puertos** con `typing.Protocol` y escribir **adaptadores** intercambiables (CSV, SQLite, memoria).
  - Aplicar el patrón **repositorio** y la **inyección de dependencias**.
  - Reconocer los principios **SOLID** y cuándo aplicarlos (y cuándo no).
  - Reorganizar un proyecto real en capas y verificar la arquitectura con pruebas.
---
