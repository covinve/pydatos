/* Convierte el Markdown de las lecciones en HTML y activa los elementos interactivos.
 *
 * Además del Markdown normal, se aceptan:
 *   :::consejo / :::error / :::telco / :::capo / :::nota  [título opcional]
 *   :::comparar  con hijos :::mal y :::bien
 *   :::pasos [título]  con hijos :::paso [título]   (diagrama paso a paso)
 *   ```pyrun     bloque de código editable y ejecutable
 *   ```pytrace   visualizador: muestra cómo cambian las variables línea a línea
 *   :::reto Título   mini ejercicio dentro de la lección, con ```pyreto (código inicial),
 *                    ```pyprueba (pruebas ocultas), ```pysolucion y, opcionales, :::pista
 *                    y ```pypreparacion (código oculto que corre antes del del estudiante)
 */

const Md = (() => {
  // Los ejemplos de las lecciones tienen siempre a mano la muestra de datos del curso
  const ARCHIVOS_LECCION = ["muestra/cdr.csv", "muestra/clientes.csv", "muestra/planes.csv", "muestra/facturas.csv"];
  marked.use({ gfm: true });

  const CALLOUTS = {
    consejo: { icono: "💡", titulo: "Consejo" },
    error: { icono: "⚠️", titulo: "Error común" },
    telco: { icono: "📡", titulo: "En facturación telco" },
    capo: { icono: "🧠", titulo: "Bajo el capó" },
    nota: { icono: "📝", titulo: "Nota" },
  };
  const FALLOS_PARA_SOLUCION = 2;

  function escapar(texto) {
    return texto.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }

  /** Separa el texto en un árbol de contenedores ::: respetando los bloques de código. */
  function analizar(texto) {
    const raiz = { tipo: "raiz", hijos: [] };
    const pila = [raiz];
    let buffer = [];
    let enCodigo = false;
    const vaciar = () => {
      if (buffer.length) pila[pila.length - 1].hijos.push(buffer.join("\n"));
      buffer = [];
    };
    for (const linea of texto.split("\n")) {
      if (/^\s*(```|~~~)/.test(linea)) enCodigo = !enCodigo;
      const apertura = !enCodigo && /^:::(\w+)\s*(.*)$/.exec(linea);
      if (apertura) {
        vaciar();
        const nodo = { tipo: apertura[1], titulo: apertura[2].trim(), hijos: [] };
        pila[pila.length - 1].hijos.push(nodo);
        pila.push(nodo);
      } else if (!enCodigo && /^:::\s*$/.test(linea) && pila.length > 1) {
        vaciar();
        pila.pop();
      } else {
        buffer.push(linea);
      }
    }
    vaciar();
    return raiz;
  }

  function renderNodo(nodo) {
    if (typeof nodo === "string") return marked.parse(nodo);
    const interior = nodo.hijos.map(renderNodo).join("");
    const titulo = nodo.titulo ? marked.parseInline(nodo.titulo) : "";
    if (CALLOUTS[nodo.tipo]) {
      const c = CALLOUTS[nodo.tipo];
      return `<aside class="callout callout-${nodo.tipo}"><div class="callout-titulo"><span class="callout-icono">${c.icono}</span>${titulo || c.titulo}</div><div class="callout-cuerpo">${interior}</div></aside>`;
    }
    switch (nodo.tipo) {
      case "raiz":
        return interior;
      case "comparar":
        return `<div class="comparar">${interior}</div>`;
      case "mal":
        return `<div class="comparar-col comparar-mal"><div class="comparar-titulo">✗ ${titulo || "Evita esto"}</div>${interior}</div>`;
      case "bien":
        return `<div class="comparar-col comparar-bien"><div class="comparar-titulo">✓ ${titulo || "Mejor así"}</div>${interior}</div>`;
      case "pasos":
        return `<div class="pasos" data-titulo="${escapar(nodo.titulo)}">${interior}</div>`;
      case "paso":
        return `<div class="paso" data-titulo="${escapar(nodo.titulo)}">${interior}</div>`;
      case "columnas":
        return `<div class="columnas">${interior}</div>`;
      case "columna":
        return `<div class="columna">${titulo ? `<div class="columna-titulo">${titulo}</div>` : ""}${interior}</div>`;
      case "reto":
        return `<section class="reto" data-titulo="${escapar(nodo.titulo)}">${interior}</section>`;
      default:
        return `<div class="bloque-${nodo.tipo}">${interior}</div>`;
    }
  }

  function render(texto) {
    return renderNodo(analizar(texto || ""));
  }

  // -------------------------------------------------------------------------
  // Activación de elementos interactivos
  // -------------------------------------------------------------------------

  /** Activa los elementos interactivos. `opciones.leccion` da identidad a los retos para guardar el progreso. */
  function activar(contenedor, opciones = {}) {
    contenedor.querySelectorAll("section.reto").forEach((seccion, i) => {
      crearReto(seccion, opciones.leccion ? `${opciones.leccion}-r${i + 1}` : null);
    });
    contenedor.querySelectorAll("pre code").forEach((bloque) => {
      const clase = [...bloque.classList].find((c) => c.startsWith("language-")) || "";
      const lenguaje = clase.replace("language-", "");
      if (lenguaje === "pyrun") return crearEjecutable(bloque.closest("pre"), bloque.textContent);
      if (lenguaje === "pytrace") return crearTraza(bloque.closest("pre"), bloque.textContent);
      if (lenguaje && hljs.getLanguage(lenguaje)) hljs.highlightElement(bloque);
      else if (!lenguaje) bloque.classList.add("hljs");
      agregarCopiar(bloque.closest("pre"));
    });
    contenedor.querySelectorAll(".pasos").forEach(crearPasos);
    contenedor.querySelectorAll("table").forEach((tabla) => {
      if (tabla.parentElement.classList.contains("tabla-scroll")) return;
      const envoltura = document.createElement("div");
      envoltura.className = "tabla-scroll";
      tabla.replaceWith(envoltura);
      envoltura.appendChild(tabla);
    });
    contenedor.querySelectorAll("a[href^='http']").forEach((a) => {
      a.target = "_blank";
      a.rel = "noopener";
    });
  }

  function agregarCopiar(pre) {
    if (!pre || pre.querySelector(".copiar")) return;
    const boton = document.createElement("button");
    boton.className = "copiar";
    boton.type = "button";
    boton.textContent = "Copiar";
    boton.addEventListener("click", () => {
      navigator.clipboard.writeText(pre.querySelector("code").textContent.replace(/\n$/, ""));
      boton.textContent = "¡Copiado!";
      setTimeout(() => (boton.textContent = "Copiar"), 1500);
    });
    pre.appendChild(boton);
  }

  /** Crea un editor CodeMirror. */
  function crearEditor(elemento, codigo, opciones = {}) {
    const editor = CodeMirror(elemento, {
      value: codigo,
      mode: "python",
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      matchBrackets: true,
      autoCloseBrackets: true,
      viewportMargin: Infinity,
      readOnly: opciones.soloLectura || false,
      extraKeys: {
        Tab: (cm) => (cm.somethingSelected() ? cm.indentSelection("add") : cm.replaceSelection("    ", "end")),
        "Shift-Tab": (cm) => cm.indentSelection("subtract"),
        "Ctrl-Enter": () => opciones.alEjecutar && opciones.alEjecutar(),
        "Cmd-Enter": () => opciones.alEjecutar && opciones.alEjecutar(),
        "Ctrl-/": "toggleComment",
      },
    });
    return editor;
  }

  /** Muestra el resultado de una ejecución en un panel. */
  function pintarResultado(panel, resultado) {
    panel.innerHTML = "";
    panel.hidden = false;
    if (resultado.salida) {
      const pre = document.createElement("pre");
      pre.className = "salida-texto";
      pre.textContent = resultado.salida;
      panel.appendChild(pre);
    }
    (resultado.figuras || []).forEach((png) => {
      const img = document.createElement("img");
      img.className = "salida-figura";
      img.alt = "Gráfico generado por el código";
      img.src = "data:image/png;base64," + png;
      panel.appendChild(img);
    });
    if (resultado.error) {
      const div = document.createElement("div");
      div.className = "salida-error";
      div.innerHTML = `<strong>${resultado.sintaxis ? "Error de sintaxis" : "Error"}</strong><pre></pre>`;
      div.querySelector("pre").textContent = resultado.error;
      panel.appendChild(div);
    }
    if (!panel.childNodes.length) {
      panel.innerHTML = '<div class="salida-vacia">El código se ejecutó sin imprimir nada.</div>';
    }
  }

  function crearEjecutable(pre, codigo) {
    codigo = codigo.replace(/\n$/, "");
    const caja = document.createElement("div");
    caja.className = "ejecutable";
    caja.innerHTML = `
      <div class="ejecutable-barra">
        <span class="ejecutable-etiqueta">Python · editable</span>
        <span class="ejecutable-estado"></span>
        <button type="button" class="boton boton-chico boton-fantasma" data-accion="restaurar" title="Volver al código original">↺ Restaurar</button>
        <button type="button" class="boton boton-chico boton-primario" data-accion="ejecutar" title="Ctrl + Enter">▶ Ejecutar</button>
      </div>
      <div class="ejecutable-editor"></div>
      <div class="ejecutable-salida" hidden></div>`;
    pre.replaceWith(caja);
    const estado = caja.querySelector(".ejecutable-estado");
    const panel = caja.querySelector(".ejecutable-salida");
    const botonEjecutar = caja.querySelector('[data-accion="ejecutar"]');
    const correr = async () => {
      botonEjecutar.disabled = true;
      estado.textContent = "Preparando…";
      const resultado = await Py.ejecutar({
        codigo: editor.getValue(),
        archivos: ARCHIVOS_LECCION,
        alAvanzar: (t) => (estado.textContent = t),
      });
      estado.textContent = "";
      botonEjecutar.disabled = false;
      pintarResultado(panel, resultado);
    };
    const editor = crearEditor(caja.querySelector(".ejecutable-editor"), codigo, { alEjecutar: correr });
    botonEjecutar.addEventListener("click", correr);
    caja.querySelector('[data-accion="restaurar"]').addEventListener("click", () => {
      editor.setValue(codigo);
      panel.hidden = true;
    });
    Py.precalentar();
  }

  /** Mini ejercicio dentro de la lección: se escribe, se comprueba y, si hace falta, se abre la pista o la solución. */
  function crearReto(seccion, id) {
    const extraer = (lenguaje) => {
      const bloque = seccion.querySelector(`pre > code.language-${lenguaje}`);
      if (!bloque) return "";
      bloque.closest("pre").remove();
      return bloque.textContent.replace(/\n$/, "");
    };
    const inicial = extraer("pyreto");
    const pruebas = extraer("pyprueba");
    const solucion = extraer("pysolucion");
    const preparacion = extraer("pypreparacion");
    const bloquePista = seccion.querySelector(":scope > .bloque-pista");
    const pista = bloquePista ? bloquePista.innerHTML : "";
    if (bloquePista) bloquePista.remove();

    const enunciado = document.createElement("div");
    enunciado.className = "reto-enunciado";
    enunciado.append(...seccion.childNodes);
    seccion.innerHTML = `
      <div class="reto-cabecera">
        <span class="reto-icono">🎯</span>
        <span class="reto-titulo"><small>Pruébalo tú</small>${marked.parseInline(seccion.dataset.titulo || "")}</span>
        <span class="reto-insignia"></span>
      </div>`;
    seccion.appendChild(enunciado);
    seccion.insertAdjacentHTML("beforeend", `
      <div class="editor-caja reto-editor">
        <div class="editor-barra">
          <span class="ejecutable-etiqueta">Python · tu turno</span>
          <span class="ejecutable-estado"></span>
        </div>
        <div class="reto-codigo"></div>
        <div class="editor-acciones">
          <button type="button" class="boton boton-chico boton-fantasma" data-accion="reiniciar" title="Volver al código inicial">↺ Reiniciar</button>
          <span class="espaciador"></span>
          <button type="button" class="boton boton-chico" data-accion="ejecutar" title="Ctrl + Enter · solo muestra lo que imprime">▶ Ejecutar</button>
          <button type="button" class="boton boton-chico boton-primario" data-accion="comprobar">✔ Comprobar</button>
        </div>
      </div>
      <div class="reto-resultado" hidden></div>
      <div class="reto-ayudas"></div>`);

    let sinGuardar = { resuelto: false, fallos: 0 };
    const estado = () => (id ? Progreso.reto(id) : sinGuardar);
    const registrar = (ok) => {
      if (id) return ok ? Progreso.retoResuelto(id) : Progreso.retoFallido(id);
      sinGuardar = ok ? { ...sinGuardar, resuelto: true } : { ...sinGuardar, fallos: sinGuardar.fallos + 1 };
      return sinGuardar;
    };
    const estadoEl = seccion.querySelector(".ejecutable-estado");
    const resultadoEl = seccion.querySelector(".reto-resultado");
    const ayudas = seccion.querySelector(".reto-ayudas");
    const insignia = seccion.querySelector(".reto-insignia");
    const botones = [...seccion.querySelectorAll(".editor-acciones .boton")];

    function pintarAyudas() {
      const e = estado();
      const verSolucion = e.resuelto || e.fallos >= FALLOS_PARA_SOLUCION;
      const verPista = pista && (e.resuelto || e.fallos >= 1);
      let html = "";
      if (verPista) {
        html += `<details class="ayuda" ${verSolucion ? "" : "open"}><summary>💡 Pista</summary><div class="contenido">${pista}</div></details>`;
      }
      if (verSolucion) {
        html += `<details class="ayuda ayuda-solucion"><summary>📘 Solución</summary><div class="contenido"><pre><code class="language-python">${escapar(solucion)}</code></pre></div></details>`;
      }
      ayudas.innerHTML = html;
      ayudas.querySelectorAll("pre code").forEach((b) => hljs.highlightElement(b));
      insignia.innerHTML = e.resuelto ? '<span class="chip chip-ok">✅ Resuelto</span>' : "";
    }

    function pintarComprobacion(resultado) {
      resultadoEl.hidden = false;
      if (!resultado.ok) {
        resultadoEl.innerHTML = `<div class="salida-error"><pre>${escapar(resultado.error)}</pre></div>`;
        return;
      }
      if (resultado.sintaxis) {
        resultadoEl.innerHTML = `<div class="resultado-cabecera resultado-aviso">✏️ Hay un error de sintaxis. <small>No cuenta como intento: corrígelo y vuelve a comprobar.</small></div><div class="salida-error"><pre>${escapar(resultado.error)}</pre></div>`;
        return;
      }
      const lista = resultado.pruebas || [];
      const ok = !resultado.error && lista.length > 0 && lista.every((p) => p.ok);
      const yaResuelto = estado().resuelto;
      const e = registrar(ok);
      let html;
      if (ok) {
        html = `<div class="resultado-cabecera resultado-ok">🎉 ¡Reto superado! <small>Abajo puedes comparar tu código con la solución.</small></div>`;
      } else {
        const pasadas = lista.filter((p) => p.ok).length;
        const ayuda = yaResuelto
          ? "Ya lo habías resuelto antes; esta versión no pasa todas las comprobaciones."
          : e.fallos >= FALLOS_PARA_SOLUCION
            ? "Ya puedes ver la solución abajo. Léela, cierra y vuelve a escribirlo tú."
            : pista
              ? "Se desbloqueó una pista abajo."
              : "Lee el mensaje y vuelve a intentarlo.";
        html = `<div class="resultado-cabecera resultado-fallo">${lista.length ? `${pasadas} de ${lista.length} comprobaciones pasaron.` : "Tu código lanzó un error."} <small>${ayuda}</small></div>`;
      }
      if (resultado.error) html += `<div class="salida-error"><strong>Error al ejecutar tu código</strong><pre>${escapar(resultado.error)}</pre></div>`;
      if (lista.length) {
        html += `<ul class="pruebas">${lista
          .map((p) => `<li class="${p.ok ? "prueba-ok" : "prueba-fallo"}"><span class="prueba-icono">${p.ok ? "✓" : "✗"}</span><div><b>${escapar(p.nombre)}</b>${p.mensaje ? `<pre>${escapar(p.mensaje)}</pre>` : ""}</div></li>`)
          .join("")}</ul>`;
      }
      if (resultado.salida) html += `<details class="salida-detalle" ${ok ? "" : "open"}><summary>Lo que imprimió tu código</summary><pre class="salida-texto">${escapar(resultado.salida)}</pre></details>`;
      resultadoEl.innerHTML = html;
      pintarAyudas();
    }

    async function correr(modo) {
      botones.forEach((b) => (b.disabled = true));
      estadoEl.textContent = "Preparando…";
      const resultado = await Py.ejecutar({
        tipo: modo,
        codigo: editor.getValue(),
        pruebas,
        preparacion,
        archivos: ARCHIVOS_LECCION,
        alAvanzar: (t) => (estadoEl.textContent = t),
      });
      estadoEl.textContent = "";
      botones.forEach((b) => (b.disabled = false));
      if (id) Progreso.guardarCodigoReto(id, editor.getValue());
      if (modo === "probar") return pintarComprobacion(resultado);
      resultadoEl.hidden = false;
      resultadoEl.innerHTML = '<div class="ejecutable-salida"></div>';
      pintarResultado(resultadoEl.firstChild, resultado);
    }

    const guardado = id ? estado().codigo : null;
    const editor = crearEditor(seccion.querySelector(".reto-codigo"), guardado ?? inicial, { alEjecutar: () => correr("ejecutar") });
    let temporizador = null;
    editor.on("change", () => {
      if (!id) return;
      clearTimeout(temporizador);
      temporizador = setTimeout(() => Progreso.guardarCodigoReto(id, editor.getValue()), 600);
    });
    seccion.querySelector('[data-accion="ejecutar"]').addEventListener("click", () => correr("ejecutar"));
    seccion.querySelector('[data-accion="comprobar"]').addEventListener("click", () => correr("probar"));
    seccion.querySelector('[data-accion="reiniciar"]').addEventListener("click", () => {
      if (editor.getValue() !== inicial && !confirm("¿Volver al código inicial? Perderás lo que escribiste.")) return;
      editor.setValue(inicial);
      resultadoEl.hidden = true;
    });
    pintarAyudas();
    Py.precalentar();
  }

  function crearTraza(pre, codigo) {
    codigo = codigo.replace(/\n$/, "");
    const lineas = codigo.split("\n");
    const caja = document.createElement("div");
    caja.className = "traza";
    caja.innerHTML = `
      <div class="traza-barra">
        <span class="ejecutable-etiqueta">🔍 Visualizador paso a paso</span>
        <span class="traza-estado"></span>
        <button type="button" class="boton boton-chico boton-primario" data-accion="iniciar">▶ Ver la ejecución</button>
      </div>
      <div class="traza-cuerpo">
        <ol class="traza-codigo">${lineas.map((l) => `<li><code>${escapar(l) || " "}</code></li>`).join("")}</ol>
        <div class="traza-panel">
          <div class="traza-pila"></div>
          <div class="traza-vars"><p class="traza-ayuda">Pulsa <b>Ver la ejecución</b> y avanza línea por línea para ver cómo cambian las variables.</p></div>
          <div class="traza-salida-titulo">Salida</div>
          <pre class="traza-salida"></pre>
        </div>
      </div>
      <div class="traza-controles" hidden>
        <button type="button" class="boton boton-chico" data-accion="primero" title="Inicio">⏮</button>
        <button type="button" class="boton boton-chico" data-accion="anterior" title="Paso anterior">◀ Anterior</button>
        <input type="range" min="0" value="0" class="traza-deslizador" aria-label="Paso">
        <span class="traza-contador"></span>
        <button type="button" class="boton boton-chico boton-primario" data-accion="siguiente" title="Paso siguiente">Siguiente ▶</button>
        <button type="button" class="boton boton-chico" data-accion="ultimo" title="Final">⏭</button>
      </div>`;
    pre.replaceWith(caja);
    hljs.highlightElement && caja.querySelectorAll(".traza-codigo code").forEach((c) => {
      c.innerHTML = hljs.highlight(c.textContent, { language: "python" }).value;
    });

    const items = caja.querySelectorAll(".traza-codigo li");
    const vars = caja.querySelector(".traza-vars");
    const pilaEl = caja.querySelector(".traza-pila");
    const salida = caja.querySelector(".traza-salida");
    const deslizador = caja.querySelector(".traza-deslizador");
    const contador = caja.querySelector(".traza-contador");
    const estado = caja.querySelector(".traza-estado");
    let pasos = [];
    let indice = 0;
    let anteriores = {};

    function tablaVars(titulo, objeto, previo) {
      const filas = Object.entries(objeto)
        .map(([k, v]) => {
          const cambio = previo && previo[k] !== v ? " cambio" : "";
          return `<tr class="${cambio}"><td class="var-nombre">${escapar(k)}</td><td class="var-valor"><code>${escapar(v)}</code></td></tr>`;
        })
        .join("");
      return `<div class="traza-tabla-titulo">${titulo}</div>${
        filas ? `<table class="traza-tabla">${filas}</table>` : '<p class="traza-ayuda">(sin variables todavía)</p>'
      }`;
    }

    function mostrar(i) {
      indice = Math.max(0, Math.min(i, pasos.length - 1));
      const paso = pasos[indice];
      const previo = indice > 0 ? pasos[indice - 1] : null;
      items.forEach((li, n) => li.classList.toggle("actual", n + 1 === paso.linea));
      const enFuncion = paso.pila.length > 1;
      let html = "";
      if (enFuncion) html += tablaVars(`Variables de <code>${escapar(paso.pila[paso.pila.length - 1])}()</code>`, paso.locales, previo && previo.locales);
      html += tablaVars(enFuncion ? "Variables del programa" : "Variables", paso.globales, previo && previo.globales);
      if (paso.retorno !== null && paso.retorno !== undefined) html += `<div class="traza-retorno">↩ devuelve <code>${escapar(paso.retorno)}</code></div>`;
      vars.innerHTML = html;
      pilaEl.innerHTML = paso.pila.map((p) => `<span class="pila-item">${escapar(p)}</span>`).join('<span class="pila-flecha">→</span>');
      salida.textContent = paso.salida || "";
      deslizador.value = indice;
      const ultimo = indice === pasos.length - 1;
      contador.textContent = paso.linea === 0 ? "Fin del programa" : `Paso ${indice + 1} de ${pasos.length - 1}`;
      if (ultimo && anteriores.error) {
        vars.innerHTML += `<div class="salida-error"><strong>Error</strong><pre>${escapar(anteriores.error)}</pre></div>`;
      }
      const lineaActual = items[paso.linea - 1];
      if (lineaActual) lineaActual.scrollIntoView({ block: "nearest" });
    }

    caja.querySelector('[data-accion="iniciar"]').addEventListener("click", async (e) => {
      const boton = e.currentTarget;
      boton.disabled = true;
      estado.textContent = "Preparando…";
      const resultado = await Py.ejecutar({ tipo: "trazar", codigo, alAvanzar: (t) => (estado.textContent = t) });
      boton.disabled = false;
      estado.textContent = resultado.limite ? "Se muestran los primeros 500 pasos" : "";
      if (!resultado.pasos || !resultado.pasos.length) {
        vars.innerHTML = `<div class="salida-error"><pre>${escapar(resultado.error || "No se pudo visualizar")}</pre></div>`;
        return;
      }
      pasos = resultado.pasos;
      if (resultado.salida_final !== undefined) {
        pasos.push({ ...pasos[pasos.length - 1], linea: 0, salida: resultado.salida_final, retorno: null, pila: ["programa"], locales: {} });
      }
      anteriores = resultado;
      deslizador.max = pasos.length - 1;
      caja.querySelector(".traza-controles").hidden = false;
      boton.textContent = "↺ Reiniciar";
      mostrar(0);
    });
    caja.querySelector('[data-accion="primero"]').addEventListener("click", () => mostrar(0));
    caja.querySelector('[data-accion="anterior"]').addEventListener("click", () => mostrar(indice - 1));
    caja.querySelector('[data-accion="siguiente"]').addEventListener("click", () => mostrar(indice + 1));
    caja.querySelector('[data-accion="ultimo"]').addEventListener("click", () => mostrar(pasos.length - 1));
    deslizador.addEventListener("input", () => mostrar(Number(deslizador.value)));
  }

  /** Diagrama paso a paso: muestra un paso a la vez con controles. */
  function crearPasos(caja) {
    if (caja.dataset.activo) return;
    caja.dataset.activo = "1";
    const pasos = [...caja.querySelectorAll(":scope > .paso")];
    if (!pasos.length) return;
    const titulo = caja.dataset.titulo;
    const cabecera = document.createElement("div");
    cabecera.className = "pasos-cabecera";
    cabecera.innerHTML = `<span class="pasos-icono">🎞️</span><span class="pasos-titulo">${titulo ? marked.parseInline(titulo) : "Paso a paso"}</span>`;
    const controles = document.createElement("div");
    controles.className = "pasos-controles";
    controles.innerHTML = `
      <button type="button" class="boton boton-chico" data-accion="anterior">◀</button>
      <div class="pasos-puntos">${pasos.map((_, i) => `<button type="button" class="pasos-punto" data-i="${i}" aria-label="Paso ${i + 1}"></button>`).join("")}</div>
      <button type="button" class="boton boton-chico" data-accion="siguiente">▶</button>
      <button type="button" class="boton boton-chico boton-fantasma" data-accion="reproducir">⏵ Reproducir</button>`;
    const subtitulo = document.createElement("div");
    subtitulo.className = "pasos-subtitulo";
    caja.prepend(cabecera);
    cabecera.after(subtitulo);
    caja.appendChild(controles);
    let actual = 0;
    let reloj = null;
    const ir = (i) => {
      actual = (i + pasos.length) % pasos.length;
      pasos.forEach((p, n) => p.classList.toggle("visible", n === actual));
      controles.querySelectorAll(".pasos-punto").forEach((p, n) => p.classList.toggle("activo", n === actual));
      const t = pasos[actual].dataset.titulo;
      subtitulo.innerHTML = `<b>Paso ${actual + 1}/${pasos.length}</b>${t ? " · " + marked.parseInline(t) : ""}`;
    };
    const detener = () => {
      clearInterval(reloj);
      reloj = null;
      controles.querySelector('[data-accion="reproducir"]').textContent = "⏵ Reproducir";
    };
    controles.addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.i !== undefined) { detener(); ir(Number(b.dataset.i)); }
      if (b.dataset.accion === "anterior") { detener(); ir(actual - 1); }
      if (b.dataset.accion === "siguiente") { detener(); ir(actual + 1); }
      if (b.dataset.accion === "reproducir") {
        if (reloj) return detener();
        b.textContent = "⏸ Pausar";
        reloj = setInterval(() => {
          if (actual === pasos.length - 1) return detener();
          ir(actual + 1);
        }, 2600);
      }
    });
    ir(0);
  }

  return { render, activar, crearEditor, pintarResultado, escapar };
})();
