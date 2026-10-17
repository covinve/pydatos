---
titulo: Cómo funciona el curso
icono: 🧭
orden: 1
---

## La ruta

El curso tiene **23 módulos** en tres niveles y un **proyecto** al cierre de cada nivel. Cada módulo está pensado para una semana a tu ritmo de 2 horas diarias.

| Nivel | Módulos | Proyecto |
|---|---|---|
| 🟦 Básico | 1 a 7 | Validador de archivos de facturación |
| 🟨 Intermedio | 8 a 15 | Conciliación de facturación |
| 🟥 Avanzado | 16 a 23 | Pipeline de facturación completo |

## Una sesión típica de 2 horas

1. **20–30 min · Lección.** Lees la explicación y ejecutas los ejemplos en la misma página. Cámbialos: romper el código a propósito es la mejor forma de entenderlo.
2. **60–80 min · Ejercicios.** Resuelves los ejercicios del módulo.
3. **10–15 min · Cierre.** Revisas tu código y lo guardas con Git (`git add`, `git commit`, `git push`).

## Los elementos de las lecciones

:::consejo Así se ve un consejo
Ideas que te ahorran tiempo.
:::

:::error Así se ve un error común
Equivocaciones típicas, para que no caigas en ellas.
:::

:::telco Así se ve un caso telco
Cómo se aplica el concepto en facturación telco.
:::

:::capo Así se ve "bajo el capó"
Lo que hace Python por dentro. Es opcional, pero te da mucha claridad.
:::

Los bloques marcados **Python · editable** se pueden modificar y ejecutar con **▶ Ejecutar** (o `Ctrl + Enter`):

```pyrun
nombre = "PyDatos"
print(f"Hola desde {nombre} 🐍")
```

El **visualizador paso a paso** muestra cómo cambian las variables línea por línea:

```pytrace
total = 0
for minutos in [3, 5, 2]:
    total = total + minutos
print(total)
```

:::nota La primera vez tarda un poco
Python se descarga en tu navegador la primera vez que ejecutas código (unos segundos). Después queda en caché y es inmediato. El indicador **Python** de la barra superior se pone verde cuando está listo.
:::

## Los ejercicios

Hay dos tipos:

- **🌐 En la página:** escribes el código en el editor y pulsas **✔ Comprobar**.
- **💻 VS Code:** trabajas en tu computador, en la carpeta `ejercicios/`, y compruebas con `python comprobar.py <ejercicio>`.

Desde el nivel intermedio cada módulo trae ejercicios **🟢 básicos**, **🟡 medios** y **🔴 avanzados**.

### Los tres intentos

| Momento | Qué pasa |
|---|---|
| Fallas el intento 1 | Ves qué pruebas fallaron y se desbloquea la **pista 1**. |
| Fallas el intento 2 | Se desbloquea la **pista 2**, más concreta. |
| Fallas el intento 3 | Se desbloquea la **solución explicada**. Puedes seguir adelante. |
| Pasas las pruebas | Queda ✅ **resuelto** y puedes ver la solución para comparar. |

- **▶ Ejecutar** no gasta intentos: úsalo para probar tu código cuantas veces quieras.
- **Los errores de sintaxis no gastan intentos.**
- Lo que resuelves viendo la solución queda marcado 📖 y pasa a tu lista **Para repasar**. Vuelve a intentarlo unos días después, sin mirar.

## Tu progreso

Se guarda solo, en este navegador. Para llevarlo de la oficina a la casa usa el botón **💾** de la barra superior: exporta el archivo, súbelo con Git y en el otro computador impórtalo.

## Los proyectos

Al terminar cada nivel harás un proyecto completo por tu cuenta, en VS Code y con Git. Cada proyecto trae una **lista de criterios** para autoevaluarte. Cuando lo termines, puedes pedirle a Claude una revisión de código como la que haría un desarrollador con más experiencia.
