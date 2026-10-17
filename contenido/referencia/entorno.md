---
titulo: Trabajar en tu computador
icono: 💻
orden: 3
---

Guía rápida para tener el curso funcionando en la casa y en la oficina. El módulo 1 explica cada paso en detalle.

## Primera vez en un computador

```powershell
git clone https://github.com/TU_USUARIO/pydatos.git
cd pydatos
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python herramientas/generar_datos.py --tamano 10MB
```

:::error "La ejecución de scripts está deshabilitada en este sistema"
Si PowerShell no deja activar el entorno, ejecuta una vez (no necesita permisos de administrador):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Si tu empresa lo bloquea, no necesitas activar el entorno: usa directamente su Python, por ejemplo `.venv\Scripts\python comprobar.py m01-e1`.
:::

## Cada día

```powershell
cd pydatos
.venv\Scripts\Activate.ps1
git pull
```

Al terminar:

```powershell
git add .
git commit -m "Módulo 3: ejercicios de tarificación"
git push
```

## Ver la página del curso en tu computador

La página está publicada en GitHub Pages, pero también puedes abrirla localmente:

```powershell
python -m http.server 8000
```

y entra a <http://localhost:8000>. Necesita un servidor: abrir `index.html` con doble clic no funciona.

## Comprobar ejercicios de VS Code

```powershell
python comprobar.py --lista          # estado de todos tus ejercicios locales
python comprobar.py m06-e3           # comprobar un ejercicio
python comprobar.py m06-e3 --pista   # volver a ver las pistas desbloqueadas
```

## Sincronizar el progreso de la página

1. En la página, pulsa **💾 → Exportar progreso**.
2. Guarda `progreso-pydatos.json` en la carpeta `.progreso/` del curso.
3. `git add`, `git commit` y `git push`.
4. En el otro computador: `git pull` y **💾 → Importar progreso**.

## Docker (en casa)

Los módulos 22 y el proyecto final usan Docker. En casa, con permisos de administrador, instala **Docker Desktop** para Windows (usa WSL2) y verifica:

```powershell
docker run --rm hello-world
```

En la oficina no lo necesitas: las pruebas que usan Docker se saltan solas si no está instalado.

## GitHub Codespaces (desde la oficina, sin instalar nada)

El repositorio trae `.devcontainer/devcontainer.json`. En la página del repositorio en GitHub: **Code → Codespaces → Create codespace on main**. En uno o dos minutos tienes VS Code en el navegador con Python 3.12, las librerías del curso y Docker. Las cuentas personales incluyen horas gratuitas al mes; detén el Codespace cuando no lo uses.

:::error Solo datos del curso
Un Codespace es un servidor de GitHub: usa allí los datos **generados** del curso, nunca archivos reales de la empresa.
:::

## Si algo falla

| Problema | Solución |
|---|---|
| `python` no se reconoce | Usa `py` en lugar de `python`, o reinstala Python marcando "Add to PATH". |
| `pip install` falla por conexión o certificado | En la oficina puede haber un proxy: configúralo para tu usuario en `%APPDATA%\pip\pip.ini` (módulo 21, lección 2) con los datos que te dé sistemas. No escribas tu contraseña en comandos ni en archivos del repositorio. |
| La página no ejecuta Python | Revisa que tengas internet (Python se descarga de un CDN) y recarga con `Ctrl + F5`. |
| VS Code no encuentra el entorno | `Ctrl + Shift + P` → **Python: Select Interpreter** → elige el de `.venv`. |
