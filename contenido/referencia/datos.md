---
titulo: Datos del curso
icono: 🗂️
orden: 2
---

Todo el curso usa el mismo conjunto de datos **sintéticos** (falsos, pero realistas) de una empresa telco ficticia. Así cada módulo construye sobre lo anterior y los proyectos se parecen a tu trabajo real, sin usar datos confidenciales.

:::nota Dónde están los datos
- **En la página:** los ejercicios usan una muestra pequeña (`contenido/datos/muestra/`, 40 clientes y unos 4.000 CDR).
- **En tu computador:** los generas tú con `herramientas/generar_datos.py`, en el tamaño que quieras (10 MB, 100 MB, 1 GB, 5 GB o 20 GB). Quedan en la carpeta `datos/`, que no se sube a Git.
:::

## Cómo generarlos

Con el entorno virtual activo, desde la carpeta del curso:

```bash
python herramientas/generar_datos.py --tamano 10MB
python herramientas/generar_datos.py --tamano 1GB --formato ambos
python herramientas/generar_datos.py --tamano 20GB
```

| Opción | Qué hace |
|---|---|
| `--tamano` | Tamaño aproximado de `cdr.csv`: `10MB`, `100MB`, `1GB`, `5GB` o `20GB`. |
| `--formato` | `csv` (por defecto), `ancho` (archivo de ancho fijo) o `ambos`. |
| `--semilla` | Número que fija los datos. Con la misma semilla siempre salen los mismos datos (por defecto `2026`). |
| `--filas` | Número exacto de CDR, en lugar de `--tamano`. |

:::consejo Tiempo y espacio
Generar 1 GB toma un par de minutos. 20 GB toma entre 30 y 60 minutos y ocupa unos 20 GB (más otros 20 GB si pides `--formato ambos`). Revisa el espacio libre antes.
:::

## Los archivos

### `planes.csv` — catálogo de planes

| Columna | Descripción |
|---|---|
| `plan_id` | Código del plan: `BAS10`, `HOG30`, `HOG60`, `ILIM`, `EMP100`, `EMP300`. |
| `nombre` | Nombre comercial. |
| `segmento` | `RESIDENCIAL` o `EMPRESARIAL`. |
| `cargo_fijo` | Valor mensual del plan en pesos, sin IVA. |
| `minutos_incluidos` | Minutos de voz local y nacional incluidos. **`-1` significa ilimitado.** |
| `mb_incluidos` | Megas incluidas (`-1` = ilimitado). |
| `sms_incluidos` | Mensajes incluidos (`-1` = ilimitado). |
| `tarifa_minuto` | Precio de cada minuto local o nacional adicional. |
| `tarifa_minuto_internacional` | Precio de cada minuto internacional (nunca está incluido). |
| `tarifa_mb` | Precio de cada mega adicional. |
| `tarifa_sms` | Precio de cada SMS adicional. |

### `clientes.csv` — una línea por cliente

:::error Codificación latin-1
Este archivo viene del "sistema legado" y está guardado en **latin-1**, no en UTF-8. Si lo abres sin indicarlo, verás nombres como `GÃ³mez` o un `UnicodeDecodeError`. Léelo con `encoding="latin-1"`.
:::

| Columna | Descripción |
|---|---|
| `cliente_id` | Identificador, por ejemplo `CL0000123`. |
| `nombre` | Persona o empresa. Tiene tildes y eñes. |
| `tipo_documento` | `CC`, `CE` o `NIT`. |
| `documento` | Número de documento. |
| `segmento` | `RESIDENCIAL` o `EMPRESARIAL`. |
| `ciudad`, `region` | Ubicación del cliente. |
| `plan_id` | Plan contratado (ver `planes.csv`). |
| `linea` | Número de la línea móvil: 10 dígitos que empiezan por 3. |
| `fecha_alta` | Fecha en que el cliente se vinculó (`AAAA-MM-DD`). |
| `estado` | `ACTIVO` o `SUSPENDIDO`. Las líneas suspendidas no generan consumo. |

### `cdr.csv` — registros de consumo (Call Detail Records)

Separado por `|`, en UTF-8, con encabezado. Un registro por llamada, SMS o sesión de datos del periodo **septiembre de 2026**.

```text
cdr_id|linea_origen|linea_destino|tipo|destino|fecha_inicio|duracion_seg|mb|celda
2|3302703263|3040879936|VOZ|NACIONAL|2026-09-13 10:31:28|30|0.000|CEL97932
3|3042731004||DATOS||2026-09-11 05:04:00|1199|15.131|CEL40460
```

| Columna | Descripción |
|---|---|
| `cdr_id` | Número consecutivo del registro. |
| `linea_origen` | Línea que generó el consumo. |
| `linea_destino` | Número llamado. Vacío en `DATOS`. Los internacionales empiezan por `00`. |
| `tipo` | `VOZ`, `SMS` o `DATOS`. |
| `destino` | `LOCAL`, `NACIONAL` o `INTERNACIONAL`. Vacío en `DATOS`. |
| `fecha_inicio` | `AAAA-MM-DD HH:MM:SS`. |
| `duracion_seg` | Segundos de la llamada (en `DATOS`, duración de la sesión; en `SMS`, 0). |
| `mb` | Megas consumidas, con 3 decimales (solo en `DATOS`). |
| `celda` | Antena que atendió el consumo. |

### `cdr_ancho_fijo.txt` — los mismos CDR en ancho fijo

Muchos sistemas de facturación entregan los archivos en **ancho fijo**: sin separadores, cada campo ocupa siempre las mismas posiciones. Cada registro mide 91 caracteres:

| Campo | Posición (desde 1) | Largo | Formato |
|---|---|---|---|
| `cdr_id` | 1–12 | 12 | Relleno con ceros a la izquierda |
| `linea_origen` | 13–22 | 10 | Espacios si está vacío |
| `linea_destino` | 23–35 | 13 | Alineado a la izquierda, relleno con espacios |
| `tipo` | 36–40 | 5 | Alineado a la izquierda |
| `destino` | 41–53 | 13 | Alineado a la izquierda |
| `fecha_inicio` | 54–67 | 14 | `AAAAMMDDHHMMSS` |
| `duracion_seg` | 68–73 | 6 | Ceros a la izquierda; si es negativa: `-` y 5 dígitos |
| `mb` | 74–83 | 10 | `000123.456` |
| `celda` | 84–91 | 8 | |

:::capo Posiciones en Python
En Python las posiciones empiezan en **0**. El campo que va de la posición 13 a la 22 se lee con `registro[12:22]`.
:::

### `facturas.csv` — facturas emitidas del periodo

Una factura por cliente. **Ojo: el sistema de facturación tiene errores**. Descubrirlos es parte del curso.

| Columna | Descripción |
|---|---|
| `factura_id` | Por ejemplo `F2026090000001`. |
| `cliente_id`, `linea`, `plan_id` | A quién se facturó. |
| `periodo` | `202609`. |
| `cargo_fijo` | Cargo mensual del plan. |
| `valor_voz`, `valor_internacional`, `valor_datos`, `valor_sms` | Consumos adicionales cobrados. |
| `consumo_adicional` | Suma de los cuatro valores anteriores. |
| `descuento` | Descuento aplicado. |
| `subtotal` | `cargo_fijo + consumo_adicional - descuento`. |
| `iva` | 19 % del subtotal. |
| `total` | `subtotal + iva`. |
| `fecha_emision`, `estado_pago` | Datos de emisión. |

### `esperado.json` — las respuestas correctas

Cada conjunto de datos trae los resultados correctos: cuántos registros hay de cada tipo, cuántos errores de cada clase, los minutos y megas totales, el total que debió facturarse y cuántas facturas tienen diferencias. Compara tus programas contra este archivo.

## Reglas de negocio

Estas reglas se usan en todo el curso. Vuelve aquí cada vez que tengas dudas.

### ¿Cuándo un CDR es válido?

Un CDR es **inválido** si cumple alguna de estas condiciones (cada registro inválido tiene un solo problema):

| Error | Condición |
|---|---|
| `duplicado` | Su `cdr_id` ya apareció antes en el archivo. La primera aparición es válida; las siguientes son duplicadas. |
| `duracion_negativa` | `duracion_seg` es menor que 0. |
| `fecha_invalida` | `fecha_inicio` no es una fecha y hora reales (por ejemplo, 31 de septiembre o la hora 25). |
| `linea_vacia` | `linea_origen` está vacía. |
| `linea_desconocida` | `linea_origen` no pertenece a ningún cliente. |
| `tipo_desconocido` | `tipo` no es `VOZ`, `SMS` ni `DATOS`. |

### ¿Cómo se calcula una factura?

Para cada cliente se suman sus CDR **válidos** del periodo:

1. **Minutos nacionales:** cada llamada `VOZ` `LOCAL` o `NACIONAL` se cobra por minuto **redondeado hacia arriba**: 61 segundos son 2 minutos; 0 segundos son 0 minutos. En Python: `(segundos + 59) // 60`.
2. **Minutos internacionales:** igual, pero para destino `INTERNACIONAL`.
3. **Megas:** se suman las `mb` de todos los CDR de `DATOS` y el total se **redondea hacia arriba** a megas enteras.
4. **SMS:** se cuenta cada `SMS`.

Con eso se calcula:

| Concepto | Fórmula |
|---|---|
| `valor_voz` | `max(0, minutos_nacionales - minutos_incluidos) × tarifa_minuto`. Si el plan es ilimitado (`-1`), es 0. |
| `valor_internacional` | `minutos_internacionales × tarifa_minuto_internacional`. |
| `valor_datos` | `max(0, megas - mb_incluidos) × tarifa_mb`. Ilimitado → 0. |
| `valor_sms` | `max(0, sms - sms_incluidos) × tarifa_sms`. Ilimitado → 0. |
| `consumo_adicional` | Suma de los cuatro valores. |
| `descuento` | **10 % del cargo fijo** para clientes `EMPRESARIAL` con `fecha_alta` anterior al `2023-09-01` (tres años o más). Si no, 0. |
| `subtotal` | `cargo_fijo + consumo_adicional - descuento`. |
| `iva` | 19 % del subtotal, **redondeado al peso más cercano** (0,5 sube). |
| `total` | `subtotal + iva`. |

Todos los valores son pesos enteros.

:::telco Ejemplo completo
Cliente del plan `HOG30` (300 minutos incluidos, $120 cada minuto adicional, cargo fijo $35.900) que habló 342 minutos nacionales y nada más:

- `valor_voz = (342 − 300) × 120 = 5.040`
- `subtotal = 35.900 + 5.040 = 40.940`
- `iva = 40.940 × 0,19 = 7.778,6 → 7.779`
- `total = 48.719`
:::
