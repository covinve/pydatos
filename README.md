# 🐍 PyDatos · Python para ciencia de datos (edición telco)

Curso personal y gratuito de Python, de cero a avanzado, orientado al análisis de datos de **facturación de telecomunicaciones**: archivos planos de unos MB hasta 20 GB, CDR, conciliación, calidad de código, bases de datos, Docker y ciencia de datos aplicada.

- **23 módulos** en tres niveles (básico, intermedio y avanzado), 92 lecciones y 186 ejercicios.
- **3 proyectos**: validador de CDR, conciliación de facturación y un pipeline de facturación completo.
- Ejercicios con **validación automática**: en la página (Python corre en tu navegador con Pyodide) o en VS Code con `python comprobar.py`.
- 3 intentos por ejercicio, pistas progresivas y la solución explicada; los ejercicios que necesitaron la solución quedan marcados para repaso.
- Datos **sintéticos** generados por el propio curso (nunca uses datos reales de la empresa en este repositorio).

## Abrir el curso

**En línea:** publícalo con GitHub Pages (abajo) y entra a `https://TU_USUARIO.github.io/NOMBRE_DEL_REPOSITORIO/`.

**En tu computador:**

```powershell
python -m http.server 8000
```

y abre <http://localhost:8000>. (Con doble clic sobre `index.html` no funciona: la página necesita un servidor.)

## Preparar el entorno

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python herramientas/generar_datos.py --tamano 10MB
```

Funciona sin permisos de administrador. Para Docker (módulo 22 y proyecto final) necesitas Docker Desktop en casa, o un **GitHub Codespace** (el repositorio trae `.devcontainer/`). Más detalles en la página: *Referencia → Trabajar en tu computador*.

## Publicar en GitHub Pages

1. Crea un repositorio en GitHub y sube esta carpeta (`git init`, `git add .`, `git commit`, `git remote add origin ...`, `git push -u origin main`).
2. En el repositorio: **Settings → Pages → Build and deployment → Source: Deploy from a branch**, rama `main`, carpeta `/ (root)`, **Save**.
3. En uno o dos minutos la página queda en `https://TU_USUARIO.github.io/NOMBRE_DEL_REPOSITORIO/`.

No hay que compilar nada: `contenido/curso.json` ya está generado. Si editas el contenido (`contenido/**/*.md`), regenera con `python herramientas/construir.py` antes de subir.

## Estructura

| Carpeta | Contenido |
|---|---|
| `index.html`, `assets/` | La página del curso (HTML, CSS y JavaScript, sin compilación) |
| `contenido/` | Lecciones, ejercicios y proyectos en Markdown, y `curso.json` generado |
| `contenido/datos/muestra/` | Datos pequeños que usan los ejercicios de la página |
| `ejercicios/` | Ejercicios de VS Code (`mXX-eY/`), con sus pruebas |
| `proyectos/` | Los tres proyectos, con su estructura y pruebas de contrato |
| `herramientas/` | `generar_datos.py` (datos de 10 MB a 20 GB), `construir.py` y `validar.py` |
| `comprobar.py` | Comprueba tus ejercicios de VS Code: `python comprobar.py m06-e3` |
| `datos/` | Datos generados en tu computador (no se suben a Git) |

## Para quien mantiene el curso

```powershell
python herramientas/construir.py          # Markdown → contenido/curso.json
python herramientas/validar.py            # verifica que cada solución pasa sus pruebas y cada inicial no
python herramientas/validar.py m16        # solo un módulo
```

## Licencia

Material de estudio personal. Los datos son ficticios y generados aleatoriamente.
