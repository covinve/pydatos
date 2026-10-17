---
numero: 21
nivel: avanzado
titulo: Configuración y dependencias
icono: ⚙️
resumen: Que tu proyecto funcione igual en la oficina, en casa, en GitHub Actions y en Docker. Versiones y archivos de bloqueo con pip-tools y uv, configuración por capas (TOML, .env, variables de entorno), secretos fuera del código y validación con pydantic-settings.
objetivos:
  - Declarar dependencias en `pyproject.toml` con **especificadores de versión** adecuados.
  - **Congelar** el entorno exacto con un archivo de bloqueo (`pip-compile`, `uv lock`) y reproducirlo.
  - Usar **uv** (sin permisos de administrador) y conocer Poetry.
  - Separar la **configuración** del código: valores por defecto, archivo TOML, `.env`, variables de entorno y argumentos, con una **precedencia** clara.
  - Manejar **secretos** sin que lleguen nunca a Git ni a los registros.
  - Validar la configuración al arrancar con **pydantic-settings**.
---
