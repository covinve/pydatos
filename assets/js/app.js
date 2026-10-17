/* Aplicación principal: carga el curso, dibuja las vistas y maneja la navegación. */

const App = (() => {
  const NIVELES = {
    basico: { nombre: "Básico", icono: "🟦", clase: "nivel-basico" },
    intermedio: { nombre: "Intermedio", icono: "🟨", clase: "nivel-intermedio" },
    avanzado: { nombre: "Avanzado", icono: "🟥", clase: "nivel-avanzado" },
  };
  const DIFICULTAD = {
    basico: { nombre: "Básico", icono: "🟢" },
    medio: { nombre: "Medio", icono: "🟡" },
    avanzado: { nombre: "Avanzado", icono: "🔴" },
    reto: { nombre: "Ejercicio", icono: "🎯" },
  };
  const ESTADOS = {
    nuevo: { icono: "○", texto: "Sin empezar", clase: "estado-nuevo" },
    en_curso: { icono: "◐", texto: "En curso", clase: "estado-curso" },
    solucion: { icono: "📖", texto: "Visto con solución", clase: "estado-solucion" },
    resuelto: { icono: "✅", texto: "Resuelto", clase: "estado-resuelto" },
  };

  let curso = null;
  const indice = { modulos: {}, lecciones: {}, ejercicios: {}, proyectos: {}, referencias: {} };
  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const esc = (t) => Md.escapar(String(t ?? ""));

  // -------------------------------------------------------------------------
  // Carga
  // -------------------------------------------------------------------------

  async function iniciar() {
    aplicarTema(localStorage.getItem("pydatos.tema") || "auto");
    try {
      const respuesta = await fetch("contenido/curso.json", { cache: "no-cache" });
      curso = await respuesta.json();
    } catch {
      $("#vista").innerHTML = `<div class="tarjeta aviso-carga"><h2>No se pudo cargar el curso</h2>
        <p>Esta página necesita abrirse desde un servidor web, no haciendo doble clic en el archivo.</p>
        <p>En la carpeta del curso ejecuta:</p><pre><code>python -m http.server 8000</code></pre>
        <p>y abre <a href="http://localhost:8000">http://localhost:8000</a>.</p></div>`;
      return;
    }
    for (const m of curso.modulos) {
      indice.modulos[m.id] = m;
      m.lecciones.forEach((l, i) => (indice.lecciones[l.id] = { ...l, modulo: m, posicion: i }));
      m.ejercicios.forEach((e, i) => (indice.ejercicios[e.id] = { ...e, modulo: m, posicion: i }));
    }
    curso.proyectos.forEach((p) => (indice.proyectos[p.id] = p));
    curso.referencias.forEach((r) => (indice.referencias[r.id] = r));

    configurarInterfaz();
    Progreso.alCambiar(() => {
      pintarMenu();
      pintarRacha();
    });
    pintarMenu();
    pintarRacha();
    window.addEventListener("hashchange", enrutar);
    enrutar();
  }

  function configurarInterfaz() {
    $("#boton-tema").addEventListener("click", () => {
      const orden = ["auto", "claro", "oscuro"];
      const actual = localStorage.getItem("pydatos.tema") || "auto";
      const siguiente = orden[(orden.indexOf(actual) + 1) % orden.length];
      localStorage.setItem("pydatos.tema", siguiente);
      aplicarTema(siguiente);
    });
    $("#boton-menu").addEventListener("click", () => document.body.classList.toggle("menu-abierto"));
    $("#velo").addEventListener("click", () => document.body.classList.remove("menu-abierto"));
    $("#boton-progreso").addEventListener("click", abrirDialogoProgreso);
    Py.alCambiarEstado((estado, texto) => {
      const indicador = $("#estado-python");
      indicador.dataset.estado = estado;
      indicador.title = estado === "listo" ? "Python listo" : estado === "cargando" ? texto || "Cargando Python…" : "Python se cargará al usarlo";
    });
  }

  function aplicarTema(tema) {
    const raiz = document.documentElement;
    if (tema === "auto") raiz.removeAttribute("data-theme");
    else raiz.setAttribute("data-theme", tema === "oscuro" ? "dark" : "light");
    const boton = $("#boton-tema");
    if (boton) {
      boton.textContent = { auto: "🌗", claro: "☀️", oscuro: "🌙" }[tema];
      boton.title = { auto: "Tema: automático", claro: "Tema: claro", oscuro: "Tema: oscuro" }[tema];
    }
  }

  // -------------------------------------------------------------------------
  // Cálculos de progreso
  // -------------------------------------------------------------------------

  function progresoModulo(m) {
    const lecciones = m.lecciones.filter((l) => Progreso.leccion(l.id)?.completada).length;
    let resueltos = 0;
    let conSolucion = 0;
    for (const e of m.ejercicios) {
      const estado = Progreso.ejercicio(e.id).estado;
      if (estado === "resuelto") resueltos++;
      if (estado === "solucion") conSolucion++;
    }
    const total = m.lecciones.length + m.ejercicios.length;
    const hechos = lecciones + resueltos + conSolucion;
    return {
      lecciones,
      resueltos,
      conSolucion,
      porcentaje: total ? Math.round((hechos / total) * 100) : 0,
      completo: total > 0 && hechos === total,
      perfecto: total > 0 && lecciones + resueltos === total,
    };
  }

  function retosResueltos(l) {
    let resueltos = 0;
    for (let i = 1; i <= (l.retos || 0); i++) if (Progreso.reto(`${l.id}-r${i}`).resuelto) resueltos++;
    return resueltos;
  }

  function progresoNivel(nivel) {
    const modulos = curso.modulos.filter((m) => m.nivel === nivel);
    let total = 0;
    let hechos = 0;
    for (const m of modulos) {
      const p = progresoModulo(m);
      total += m.lecciones.length + m.ejercicios.length;
      hechos += p.lecciones + p.resueltos + p.conSolucion;
    }
    return { modulos, porcentaje: total ? Math.round((hechos / total) * 100) : 0 };
  }

  function progresoProyecto(p) {
    const estado = Progreso.proyecto(p.id);
    const marcados = Object.values(estado.criterios || {}).filter(Boolean).length;
    return { marcados, total: p.criterios.length, terminado: estado.estado === "terminado", estado: estado.estado };
  }

  // -------------------------------------------------------------------------
  // Menú lateral
  // -------------------------------------------------------------------------

  function anillo(porcentaje, tamano = 22) {
    const r = tamano / 2 - 2.5;
    const c = 2 * Math.PI * r;
    return `<svg class="anillo" width="${tamano}" height="${tamano}" viewBox="0 0 ${tamano} ${tamano}" aria-hidden="true">
      <circle cx="${tamano / 2}" cy="${tamano / 2}" r="${r}" class="anillo-fondo"/>
      <circle cx="${tamano / 2}" cy="${tamano / 2}" r="${r}" class="anillo-valor" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - porcentaje / 100)}"/>
    </svg>`;
  }

  function pintarMenu() {
    if (!curso) return;
    const ruta = location.hash || "#/";
    let html = `<a class="menu-item ${ruta === "#/" ? "activo" : ""}" href="#/"><span class="menu-icono">🏠</span>Inicio</a>
      <a class="menu-item ${ruta === "#/repaso" ? "activo" : ""}" href="#/repaso"><span class="menu-icono">🔁</span>Para repasar <span class="menu-insignia" id="cuenta-repaso"></span></a>`;
    for (const [clave, nivel] of Object.entries(NIVELES)) {
      const pn = progresoNivel(clave);
      html += `<div class="menu-seccion ${nivel.clase}"><span>${nivel.icono} Nivel ${nivel.nombre}</span><span class="menu-porcentaje">${pn.porcentaje}%</span></div>`;
      for (const m of pn.modulos) {
        const p = progresoModulo(m);
        const activo = ruta.includes(`/${m.id}`) ? "activo" : "";
        html += `<a class="menu-item menu-modulo ${activo}" href="#/modulo/${m.id}">
          <span class="menu-numero">${m.numero}</span><span class="menu-texto">${esc(m.titulo)}</span>${p.completo ? '<span class="menu-hecho">✓</span>' : anillo(p.porcentaje)}</a>`;
      }
      for (const pr of curso.proyectos.filter((x) => x.nivel === clave)) {
        const pp = progresoProyecto(pr);
        html += `<a class="menu-item menu-proyecto ${ruta === "#/proyecto/" + pr.id ? "activo" : ""}" href="#/proyecto/${pr.id}">
          <span class="menu-icono">🏁</span><span class="menu-texto">${esc(pr.titulo)}</span>${pp.terminado ? '<span class="menu-hecho">✓</span>' : ""}</a>`;
      }
    }
    html += `<div class="menu-seccion"><span>📚 Referencia</span></div>`;
    for (const r of curso.referencias) {
      html += `<a class="menu-item ${ruta === "#/referencia/" + r.id ? "activo" : ""}" href="#/referencia/${r.id}"><span class="menu-icono">${r.icono || "📄"}</span><span class="menu-texto">${esc(r.titulo)}</span></a>`;
    }
    $("#menu").innerHTML = html;
    const repaso = listaRepaso().length;
    $("#cuenta-repaso").textContent = repaso ? repaso : "";
  }

  function pintarRacha() {
    const r = Progreso.racha();
    $("#racha").innerHTML = `🔥 <b>${r}</b> <span class="solo-ancho">${r === 1 ? "día" : "días"}</span>`;
    $("#racha").title = r ? `Llevas ${r} ${r === 1 ? "día" : "días"} seguidos estudiando` : "Estudia hoy para empezar tu racha";
  }

  function listaRepaso() {
    return Object.values(indice.ejercicios).filter((e) => Progreso.ejercicio(e.id).estado === "solucion");
  }

  // -------------------------------------------------------------------------
  // Enrutador
  // -------------------------------------------------------------------------

  function enrutar() {
    const ruta = location.hash.replace(/^#/, "") || "/";
    const [, vista, id] = ruta.split("/");
    document.body.classList.remove("menu-abierto");
    const contenedor = $("#vista");
    contenedor.className = "vista";
    let titulo = "Inicio";
    try {
      if (!vista) titulo = vistaInicio(contenedor);
      else if (vista === "modulo" && indice.modulos[id]) titulo = vistaModulo(contenedor, indice.modulos[id]);
      else if (vista === "leccion" && indice.lecciones[id]) titulo = vistaLeccion(contenedor, indice.lecciones[id]);
      else if (vista === "ejercicio" && indice.ejercicios[id]) titulo = vistaEjercicio(contenedor, indice.ejercicios[id]);
      else if (vista === "proyecto" && indice.proyectos[id]) titulo = vistaProyecto(contenedor, indice.proyectos[id]);
      else if (vista === "referencia" && indice.referencias[id]) titulo = vistaReferencia(contenedor, indice.referencias[id]);
      else if (vista === "repaso") titulo = vistaRepaso(contenedor);
      else {
        contenedor.innerHTML = `<div class="tarjeta"><h2>Página no encontrada</h2><p><a href="#/">Volver al inicio</a></p></div>`;
        titulo = "No encontrada";
      }
    } catch (error) {
      console.error(error);
      contenedor.innerHTML = `<div class="tarjeta"><h2>Algo salió mal mostrando esta página</h2><pre>${esc(error.stack || error)}</pre></div>`;
    }
    document.title = `${titulo} · PyDatos`;
    if (vista && vista !== "repaso") Progreso.recordarUltimo(location.hash);
    pintarMenu();
    window.scrollTo(0, 0);
    const activo = $("#menu .activo.menu-modulo") || $("#menu .activo");
    if (activo) activo.scrollIntoView({ block: "nearest" });
  }

  function migas(partes) {
    return `<nav class="migas">${partes
      .map((p) => (p.href ? `<a href="${p.href}">${esc(p.texto)}</a>` : `<span>${esc(p.texto)}</span>`))
      .join('<span class="migas-sep">›</span>')}</nav>`;
  }

  // -------------------------------------------------------------------------
  // Vista: inicio
  // -------------------------------------------------------------------------

  function siguientePaso() {
    for (const m of curso.modulos) {
      for (const l of m.lecciones) if (!Progreso.leccion(l.id)?.completada) return { href: `#/leccion/${l.id}`, tipo: "Lección", titulo: l.titulo, modulo: m };
      for (const e of m.ejercicios) {
        const estado = Progreso.ejercicio(e.id).estado;
        if (estado !== "resuelto" && estado !== "solucion") return { href: `#/ejercicio/${e.id}`, tipo: "Ejercicio", titulo: e.titulo, modulo: m };
      }
      const proyecto = curso.proyectos.find((p) => p.despues_de === m.numero);
      if (proyecto && !progresoProyecto(proyecto).terminado) return { href: `#/proyecto/${proyecto.id}`, tipo: "Proyecto", titulo: proyecto.titulo, modulo: m };
    }
    return null;
  }

  function vistaInicio(c) {
    const totalEj = Object.keys(indice.ejercicios).length;
    const resueltos = Object.values(indice.ejercicios).filter((e) => Progreso.ejercicio(e.id).estado === "resuelto").length;
    const totalLec = Object.keys(indice.lecciones).length;
    const lecciones = Object.values(indice.lecciones).filter((l) => Progreso.leccion(l.id)?.completada).length;
    const vistos = Object.values(indice.ejercicios).filter((e) => Progreso.ejercicio(e.id).estado === "solucion").length;
    const porcentaje = Math.round(((lecciones + resueltos + vistos) / (totalLec + totalEj)) * 100) || 0;
    const sig = siguientePaso();
    const ultimo = Progreso.datos.ultimo;
    const empezado = lecciones + resueltos + vistos > 0;

    let html = `<section class="portada">
      <div class="portada-texto">
        <div class="portada-etiqueta">Curso personal · Python para ciencia de datos</div>
        <h1>${empezado ? "¡Hola de nuevo! 👋" : "Bienvenido a PyDatos 👋"}</h1>
        <p>De cero a avanzado con datos reales de <b>facturación telco</b>: CDR, planes, facturas y archivos de hasta 20 GB.</p>
        <div class="portada-acciones">
          ${sig ? `<a class="boton boton-primario boton-grande" href="${sig.href}">${empezado ? "Continuar" : "Empezar el curso"} →</a>` : `<span class="portada-fin">🎓 ¡Terminaste el curso!</span>`}
          ${ultimo && empezado ? `<a class="boton boton-grande" href="${ultimo}">Volver a donde estaba</a>` : `<a class="boton boton-grande" href="#/referencia/como-usar">Cómo funciona</a>`}
        </div>
        ${sig ? `<div class="portada-siguiente">Siguiente: <b>${esc(sig.tipo)}</b> · ${esc(sig.titulo)} <span class="texto-suave">(Módulo ${sig.modulo.numero})</span></div>` : ""}
      </div>
      <div class="portada-anillo">${anillo(porcentaje, 150)}<div class="portada-porcentaje"><b>${porcentaje}%</b><span>del curso</span></div></div>
    </section>

    <section class="estadisticas">
      <div class="estadistica"><div class="estadistica-valor">🔥 ${Progreso.racha()}</div><div class="estadistica-nombre">días de racha</div></div>
      <div class="estadistica"><div class="estadistica-valor">${lecciones}<small>/${totalLec}</small></div><div class="estadistica-nombre">lecciones</div></div>
      <div class="estadistica"><div class="estadistica-valor">${resueltos}<small>/${totalEj}</small></div><div class="estadistica-nombre">ejercicios resueltos</div></div>
      <a class="estadistica estadistica-enlace" href="#/repaso"><div class="estadistica-valor">📖 ${vistos}</div><div class="estadistica-nombre">para repasar</div></a>
    </section>

    <h2 class="titulo-seccion">Tu ruta</h2>
    <section class="niveles">`;
    for (const [clave, nivel] of Object.entries(NIVELES)) {
      const pn = progresoNivel(clave);
      const proyectos = curso.proyectos.filter((p) => p.nivel === clave);
      html += `<div class="nivel-tarjeta ${nivel.clase}">
        <div class="nivel-cabecera"><span class="nivel-nombre">${nivel.icono} Nivel ${nivel.nombre}</span><span class="nivel-porcentaje">${pn.porcentaje}%</span></div>
        <div class="barra"><div class="barra-valor" style="width:${pn.porcentaje}%"></div></div>
        <div class="nivel-modulos">${pn.modulos
          .map((m) => {
            const p = progresoModulo(m);
            return `<a class="chip-modulo ${p.completo ? "completo" : p.porcentaje ? "empezado" : ""}" href="#/modulo/${m.id}" title="${esc(m.titulo)} · ${p.porcentaje}%"><span>${m.numero}</span>${esc(m.titulo)}</a>`;
          })
          .join("")}
          ${proyectos.map((p) => `<a class="chip-modulo chip-proyecto ${progresoProyecto(p).terminado ? "completo" : ""}" href="#/proyecto/${p.id}">🏁 ${esc(p.titulo)}</a>`).join("")}
        </div>
      </div>`;
    }
    html += `</section><h2 class="titulo-seccion">Insignias</h2><section class="insignias">`;
    for (const m of curso.modulos) {
      const p = progresoModulo(m);
      html += `<a class="insignia ${p.completo ? "ganada" : ""} ${p.perfecto ? "perfecta" : ""} ${NIVELES[m.nivel].clase}" href="#/modulo/${m.id}" title="${esc(m.titulo)}${p.completo ? (p.perfecto ? " · ¡sin mirar soluciones!" : " · completado") : " · bloqueada"}">
        <span class="insignia-icono">${esc(m.icono || "⭐")}</span><span class="insignia-nombre">${m.numero}. ${esc(m.titulo)}</span>${p.perfecto ? '<span class="insignia-estrella">★</span>' : ""}</a>`;
    }
    for (const pr of curso.proyectos) {
      const pp = progresoProyecto(pr);
      html += `<a class="insignia insignia-proyecto ${pp.terminado ? "ganada" : ""} ${NIVELES[pr.nivel].clase}" href="#/proyecto/${pr.id}" title="${esc(pr.titulo)}"><span class="insignia-icono">🏆</span><span class="insignia-nombre">${esc(pr.titulo)}</span></a>`;
    }
    html += `</section>`;
    c.innerHTML = html;
    return "Inicio";
  }

  // -------------------------------------------------------------------------
  // Vista: módulo
  // -------------------------------------------------------------------------

  function chipDificultad(d) {
    const info = DIFICULTAD[d] || DIFICULTAD.reto;
    return `<span class="chip chip-dif-${d || "reto"}">${info.icono} ${info.nombre}</span>`;
  }

  function chipTipo(t) {
    return t === "local" ? `<span class="chip chip-local" title="Se resuelve en VS Code">💻 VS Code</span>` : `<span class="chip chip-web" title="Se resuelve en esta página">🌐 En la página</span>`;
  }

  function vistaModulo(c, m) {
    const nivel = NIVELES[m.nivel];
    const p = progresoModulo(m);
    const minutos = m.lecciones.reduce((s, l) => s + (l.minutos || 0), 0) + m.ejercicios.reduce((s, e) => s + (e.tiempo || 0), 0);
    const proyecto = curso.proyectos.find((x) => x.despues_de === m.numero);
    const anterior = curso.modulos.find((x) => x.numero === m.numero - 1);
    const siguiente = curso.modulos.find((x) => x.numero === m.numero + 1);
    let html = `${migas([{ texto: "Inicio", href: "#/" }, { texto: `Nivel ${nivel.nombre}` }, { texto: `Módulo ${m.numero}` }])}
      <header class="cabecera-modulo ${nivel.clase}">
        <div class="cabecera-icono">${esc(m.icono || "📘")}</div>
        <div class="cabecera-texto">
          <div class="cabecera-etiqueta">${nivel.icono} Nivel ${nivel.nombre} · Módulo ${m.numero}</div>
          <h1>${esc(m.titulo)}</h1>
          <p>${esc(m.resumen)}</p>
          <div class="cabecera-datos"><span>📖 ${m.lecciones.length} lecciones</span><span>🧩 ${m.ejercicios.length} ejercicios</span><span>⏱️ ~${Math.round(minutos / 60)} horas</span></div>
        </div>
        <div class="cabecera-progreso">${anillo(p.porcentaje, 84)}<span>${p.porcentaje}%</span></div>
      </header>`;
    if (m.objetivos?.length) {
      html += `<section class="tarjeta objetivos"><h3>🎯 Al terminar este módulo podrás…</h3><ul>${m.objetivos.map((o) => `<li>${marked.parseInline(o)}</li>`).join("")}</ul></section>`;
    }
    if (m.introduccion) html += `<section class="contenido intro-modulo">${Md.render(m.introduccion)}</section>`;
    html += `<h2 class="titulo-seccion">Lecciones</h2><div class="lista">`;
    m.lecciones.forEach((l, i) => {
      const hecha = Progreso.leccion(l.id)?.completada;
      const quiz = Progreso.leccion(l.id)?.quiz;
      const retos = retosResueltos(l);
      html += `<a class="fila ${hecha ? "fila-hecha" : ""}" href="#/leccion/${l.id}">
        <span class="fila-numero">${hecha ? "✓" : i + 1}</span>
        <span class="fila-texto"><b>${esc(l.titulo)}</b>${l.resumen ? `<small>${esc(l.resumen)}</small>` : ""}</span>
        <span class="fila-meta">${l.retos ? `<span class="chip ${retos === l.retos ? "chip-ok" : ""}" title="Retos resueltos">🎯 ${retos}/${l.retos}</span>` : ""}${quiz ? `<span class="chip">🧠 ${quiz.aciertos}/${quiz.total}</span>` : ""}<span class="chip">⏱️ ${l.minutos} min</span></span></a>`;
    });
    html += `</div><h2 class="titulo-seccion">Ejercicios</h2>`;
    if (m.nivel === "basico") html += `<p class="texto-suave">En el nivel básico los ejercicios van de menos a más: cada uno exige un poco más que el anterior.</p>`;
    html += `<div class="lista">`;
    m.ejercicios.forEach((e, i) => {
      const estado = Progreso.ejercicio(e.id);
      const info = ESTADOS[estado.estado] || ESTADOS.nuevo;
      html += `<a class="fila ${info.clase}" href="#/ejercicio/${e.id}">
        <span class="fila-numero">${estado.estado === "resuelto" ? "✓" : estado.estado === "solucion" ? "📖" : i + 1}</span>
        <span class="fila-texto"><b>${esc(e.titulo)}</b><small>${info.texto}${estado.intentos ? ` · ${estado.intentos} ${estado.intentos === 1 ? "intento" : "intentos"}` : ""}</small></span>
        <span class="fila-meta">${chipDificultad(e.dificultad)}${chipTipo(e.tipo)}</span></a>`;
    });
    html += `</div>`;
    if (proyecto) {
      html += `<a class="tarjeta tarjeta-proyecto" href="#/proyecto/${proyecto.id}"><div class="tarjeta-proyecto-icono">🏁</div><div><div class="cabecera-etiqueta">Proyecto de cierre del nivel</div><h3>${esc(proyecto.titulo)}</h3><p>${esc(proyecto.resumen || "")}</p></div></a>`;
    }
    html += `<nav class="paginacion">${anterior ? `<a class="boton" href="#/modulo/${anterior.id}">← Módulo ${anterior.numero}</a>` : "<span></span>"}${siguiente ? `<a class="boton" href="#/modulo/${siguiente.id}">Módulo ${siguiente.numero} →</a>` : ""}</nav>`;
    c.innerHTML = html;
    Md.activar(c);
    return `Módulo ${m.numero}: ${m.titulo}`;
  }

  // -------------------------------------------------------------------------
  // Vista: lección
  // -------------------------------------------------------------------------

  function vistaLeccion(c, l) {
    const m = l.modulo;
    const nivel = NIVELES[m.nivel];
    const anterior = m.lecciones[l.posicion - 1];
    const siguiente = m.lecciones[l.posicion + 1];
    const estado = Progreso.leccion(l.id);
    c.classList.add("vista-lectura");
    let html = `${migas([{ texto: "Inicio", href: "#/" }, { texto: `Módulo ${m.numero}: ${m.titulo}`, href: `#/modulo/${m.id}` }, { texto: `Lección ${l.posicion + 1}` }])}
      <header class="cabecera-leccion ${nivel.clase}">
        <div class="cabecera-etiqueta">Lección ${l.posicion + 1} de ${m.lecciones.length} · ⏱️ ${l.minutos} min${l.retos ? ` · 🎯 ${l.retos} ${l.retos === 1 ? "reto" : "retos"} para practicar` : ""}</div>
        <h1>${esc(l.titulo)}</h1>
        <div class="barra barra-fina"><div class="barra-valor" style="width:${((l.posicion + 1) / m.lecciones.length) * 100}%"></div></div>
      </header>
      <article class="contenido">${Md.render(l.contenido)}</article>`;
    if (l.quiz?.length) {
      html += `<section class="tarjeta quiz" id="quiz"><h2>🧠 Comprueba lo que aprendiste</h2><p class="texto-suave">Responde las ${l.quiz.length} preguntas para marcar la lección como completada.</p>`;
      l.quiz.forEach((q, i) => {
        html += `<fieldset class="pregunta" data-i="${i}"><legend><span class="pregunta-numero">${i + 1}</span>${marked.parseInline(q.pregunta)}</legend>
          ${q.opciones.map((o, j) => `<label class="opcion"><input type="radio" name="q${i}" value="${j}"><span>${marked.parseInline(o)}</span></label>`).join("")}
          <div class="pregunta-explicacion" hidden></div></fieldset>`;
      });
      html += `<div class="quiz-pie"><button type="button" class="boton boton-primario" id="calificar">Calificar</button><span id="quiz-resultado"></span></div></section>`;
    } else {
      html += `<div class="quiz-pie"><button type="button" class="boton boton-primario" id="marcar-leida">${estado?.completada ? "✓ Lección completada" : "Marcar como completada"}</button></div>`;
    }
    const primerEjercicio = m.ejercicios[0];
    html += `<nav class="paginacion">
      ${anterior ? `<a class="boton" href="#/leccion/${anterior.id}">← ${esc(anterior.titulo)}</a>` : `<a class="boton" href="#/modulo/${m.id}">← Volver al módulo</a>`}
      ${siguiente ? `<a class="boton boton-primario" href="#/leccion/${siguiente.id}">${esc(siguiente.titulo)} →</a>` : primerEjercicio ? `<a class="boton boton-primario" href="#/ejercicio/${primerEjercicio.id}">Ir a los ejercicios →</a>` : ""}
    </nav>`;
    c.innerHTML = html;
    Md.activar(c, { leccion: l.id });

    const marcar = $("#marcar-leida", c);
    if (marcar) {
      marcar.addEventListener("click", () => {
        Progreso.completarLeccion(l.id);
        marcar.textContent = "✓ Lección completada";
      });
    }
    const calificar = $("#calificar", c);
    if (calificar) {
      calificar.addEventListener("click", () => {
        let aciertos = 0;
        let respondidas = 0;
        l.quiz.forEach((q, i) => {
          const fs = c.querySelector(`.pregunta[data-i="${i}"]`);
          const elegida = fs.querySelector("input:checked");
          fs.classList.remove("correcta", "incorrecta");
          fs.querySelectorAll(".opcion").forEach((o) => o.classList.remove("opcion-correcta", "opcion-incorrecta"));
          if (!elegida) return;
          respondidas++;
          const ok = Number(elegida.value) === q.correcta;
          if (ok) aciertos++;
          fs.classList.add(ok ? "correcta" : "incorrecta");
          fs.querySelectorAll(".opcion")[q.correcta].classList.add("opcion-correcta");
          if (!ok) elegida.closest(".opcion").classList.add("opcion-incorrecta");
          const exp = fs.querySelector(".pregunta-explicacion");
          exp.hidden = false;
          exp.innerHTML = `<b>${ok ? "✓ ¡Correcto!" : "✗ No exactamente."}</b> ${marked.parseInline(q.explicacion || "")}`;
        });
        const resultado = $("#quiz-resultado", c);
        if (respondidas < l.quiz.length) {
          resultado.textContent = `Te faltan ${l.quiz.length - respondidas} por responder.`;
          return;
        }
        Progreso.completarLeccion(l.id, { aciertos, total: l.quiz.length });
        resultado.innerHTML = aciertos === l.quiz.length ? `🎉 <b>${aciertos}/${l.quiz.length}</b> ¡Perfecto! Lección completada.` : `<b>${aciertos}/${l.quiz.length}</b> · Lección completada. Revisa las explicaciones de las que fallaste.`;
      });
    }
    return l.titulo;
  }

  // -------------------------------------------------------------------------
  // Vista: ejercicio
  // -------------------------------------------------------------------------

  function vistaEjercicio(c, e) {
    const m = e.modulo;
    const nivel = NIVELES[m.nivel];
    const anterior = m.ejercicios[e.posicion - 1];
    const siguiente = m.ejercicios[e.posicion + 1];
    c.classList.add("vista-ejercicio");
    const cabecera = `${migas([{ texto: "Inicio", href: "#/" }, { texto: `Módulo ${m.numero}: ${m.titulo}`, href: `#/modulo/${m.id}` }, { texto: `Ejercicio ${e.posicion + 1}` }])}
      <header class="cabecera-ejercicio ${nivel.clase}">
        <div class="cabecera-etiqueta">Ejercicio ${e.posicion + 1} de ${m.ejercicios.length} ${chipDificultad(e.dificultad)} ${chipTipo(e.tipo)} ${e.tiempo ? `<span class="chip">⏱️ ~${e.tiempo} min</span>` : ""}</div>
        <h1>${esc(e.titulo)}</h1>
      </header>`;
    const pie = `<nav class="paginacion">
      ${anterior ? `<a class="boton" href="#/ejercicio/${anterior.id}">← Ejercicio anterior</a>` : `<a class="boton" href="#/modulo/${m.id}">← Volver al módulo</a>`}
      ${siguiente ? `<a class="boton" href="#/ejercicio/${siguiente.id}">Siguiente ejercicio →</a>` : `<a class="boton" href="#/modulo/${m.id}">Volver al módulo →</a>`}
    </nav>`;
    if (e.tipo === "local") return vistaEjercicioLocal(c, e, cabecera, pie);

    c.innerHTML = `${cabecera}
      <div class="ejercicio-grid">
        <div class="ejercicio-izquierda">
          <section class="tarjeta contenido enunciado">${Md.render(e.enunciado)}</section>
          <section id="ayudas"></section>
        </div>
        <div class="ejercicio-derecha">
          <div class="editor-caja">
            <div class="editor-barra">
              <span class="ejecutable-etiqueta">tu_solucion.py</span>
              <span class="intentos" id="intentos"></span>
              <span class="ejecutable-estado" id="estado-ejecucion"></span>
            </div>
            <div id="editor"></div>
            <div class="editor-acciones">
              <button type="button" class="boton boton-fantasma" id="reiniciar" title="Volver al código inicial">↺ Reiniciar</button>
              <span class="espaciador"></span>
              <button type="button" class="boton" id="ejecutar" title="Ctrl + Enter · no gasta intentos">▶ Ejecutar</button>
              <button type="button" class="boton boton-primario" id="comprobar">✔ Comprobar</button>
            </div>
          </div>
          <div class="tarjeta resultado" id="resultado" hidden></div>
        </div>
      </div>${pie}`;
    Md.activar(c.querySelector(".enunciado"));

    const guardado = Progreso.ejercicio(e.id).codigo;
    let temporizador = null;
    const editor = Md.crearEditor($("#editor", c), guardado ?? e.inicial, { alEjecutar: () => correr("ejecutar") });
    editor.on("change", () => {
      clearTimeout(temporizador);
      temporizador = setTimeout(() => Progreso.guardarCodigo(e.id, editor.getValue()), 600);
    });
    const estadoEl = $("#estado-ejecucion", c);
    const resultadoEl = $("#resultado", c);
    const botones = ["#ejecutar", "#comprobar"].map((s) => $(s, c));

    function pintarAyudas() {
      const estado = Progreso.ejercicio(e.id);
      const intentos = estado.intentos || 0;
      const resuelto = estado.estado === "resuelto";
      const conSolucion = estado.estado === "solucion";
      const solucionVisible = resuelto || intentos >= Progreso.MAX_INTENTOS || (conSolucion && !estado.reintento);
      const puntos = Array.from({ length: Progreso.MAX_INTENTOS }, (_, i) => `<span class="intento ${i < intentos ? "usado" : ""}"></span>`).join("");
      $("#intentos", c).innerHTML = resuelto ? `<span class="chip chip-ok">✅ Resuelto</span>` : `<span title="Intentos fallidos">${puntos}</span>`;

      let html = "";
      if (conSolucion && estado.reintento && intentos < Progreso.MAX_INTENTOS) {
        html += `<div class="aviso aviso-info">🔁 Estás repasando este ejercicio sin ayudas. Si lo resuelves, saldrá de tu lista de repaso.</div>`;
      } else if (conSolucion) {
        html += `<div class="aviso aviso-repaso">📖 Este ejercicio está en tu lista de <a href="#/repaso">repaso</a>. Cuando quieras, vuelve a intentarlo sin mirar.
          <button type="button" class="boton boton-chico" id="reintentar">Reintentar desde cero</button></div>`;
      }
      e.pistas.forEach((pista, i) => {
        const desbloqueada = intentos > i || solucionVisible;
        html += `<details class="ayuda ${desbloqueada ? "" : "bloqueada"}" ${desbloqueada && !solucionVisible && i === Math.min(intentos, e.pistas.length) - 1 ? "open" : ""}>
          <summary>${desbloqueada ? "💡" : "🔒"} Pista ${i + 1} ${desbloqueada ? "" : `<small>· se desbloquea al fallar ${i + 1} ${i ? "veces" : "vez"}</small>`}</summary>
          ${desbloqueada ? `<div class="contenido">${Md.render(pista)}</div>` : ""}</details>`;
      });
      html += `<details class="ayuda ayuda-solucion ${solucionVisible ? "" : "bloqueada"}" ${solucionVisible && !resuelto && intentos >= Progreso.MAX_INTENTOS ? "open" : ""}>
        <summary>${solucionVisible ? "📘" : "🔒"} Solución explicada ${solucionVisible ? "" : `<small>· se desbloquea al fallar ${Progreso.MAX_INTENTOS} veces o al resolverlo</small>`}</summary>
        ${solucionVisible ? `<div class="contenido"><pre><code class="language-python">${esc(e.solucion)}</code></pre>${Md.render(e.explicacion)}</div>` : ""}</details>`;
      const ayudas = $("#ayudas", c);
      ayudas.innerHTML = html;
      Md.activar(ayudas);
      const reintentar = $("#reintentar", c);
      if (reintentar) {
        reintentar.addEventListener("click", () => {
          if (!confirm("Se borrará tu código de este ejercicio y empezarás sin pistas. ¿Seguir?")) return;
          Progreso.reiniciarEjercicio(e.id);
          editor.setValue(e.inicial);
          resultadoEl.hidden = true;
          pintarAyudas();
        });
      }
    }

    async function correr(modo) {
      botones.forEach((b) => (b.disabled = true));
      estadoEl.textContent = "Preparando…";
      const resultado = await Py.ejecutar({
        tipo: modo,
        codigo: editor.getValue(),
        pruebas: e.pruebas,
        preparacion: e.preparacion,
        archivos: e.archivos,
        timeout: e.timeout ? e.timeout * 1000 : 20000,
        alAvanzar: (t) => (estadoEl.textContent = t),
      });
      estadoEl.textContent = "";
      botones.forEach((b) => (b.disabled = false));
      Progreso.guardarCodigo(e.id, editor.getValue());
      if (modo === "ejecutar") return pintarEjecucion(resultado);
      pintarComprobacion(resultado);
    }

    function pintarEjecucion(resultado) {
      resultadoEl.hidden = false;
      resultadoEl.innerHTML = `<h3>Salida</h3><div class="ejecutable-salida"></div>`;
      Md.pintarResultado(resultadoEl.querySelector(".ejecutable-salida"), resultado);
    }

    function pintarComprobacion(resultado) {
      resultadoEl.hidden = false;
      if (!resultado.ok) {
        resultadoEl.innerHTML = `<div class="salida-error"><pre>${esc(resultado.error)}</pre></div>`;
        return;
      }
      if (resultado.sintaxis) {
        resultadoEl.innerHTML = `<div class="resultado-cabecera resultado-aviso">✏️ Hay un error de sintaxis. <small>No cuenta como intento: corrígelo y vuelve a comprobar.</small></div><div class="salida-error"><pre>${esc(resultado.error)}</pre></div>`;
        return;
      }
      const pruebas = resultado.pruebas || [];
      const ok = !resultado.error && pruebas.length > 0 && pruebas.every((p) => p.ok);
      const antes = Progreso.ejercicio(e.id);
      let estado;
      if (ok) estado = Progreso.resuelto(e.id);
      else estado = Progreso.intentoFallido(e.id);
      const pasadas = pruebas.filter((p) => p.ok).length;
      let cabecera;
      if (ok) {
        cabecera = `<div class="resultado-cabecera resultado-ok">🎉 ¡Todas las pruebas pasaron! <small>${antes.estado === "solucion" ? "Este ejercicio salió de tu lista de repaso." : "Ya puedes ver la solución explicada para comparar."}</small></div>`;
      } else {
        const restantes = Math.max(0, Progreso.MAX_INTENTOS - estado.intentos);
        const mensaje = antes.estado === "resuelto"
          ? "Ya lo habías resuelto antes; esta versión no pasa todas las pruebas."
          : restantes > 0
            ? `Intento ${estado.intentos} de ${Progreso.MAX_INTENTOS}. Se desbloqueó la pista ${Math.min(estado.intentos, e.pistas.length)}.`
            : "Se desbloqueó la solución explicada. Revísala y sigue adelante: el ejercicio queda en tu lista de repaso.";
        cabecera = `<div class="resultado-cabecera resultado-fallo">${pruebas.length ? `${pasadas} de ${pruebas.length} pruebas pasaron.` : "Tu código lanzó un error."} <small>${mensaje}</small></div>`;
      }
      let html = cabecera;
      if (resultado.error) html += `<div class="salida-error"><strong>Error al ejecutar tu código</strong><pre>${esc(resultado.error)}</pre></div>`;
      if (pruebas.length) {
        html += `<ul class="pruebas">${pruebas
          .map((p) => `<li class="${p.ok ? "prueba-ok" : "prueba-fallo"}"><span class="prueba-icono">${p.ok ? "✓" : "✗"}</span><div><b>${esc(p.nombre)}</b>${p.mensaje ? `<pre>${esc(p.mensaje)}</pre>` : ""}</div></li>`)
          .join("")}</ul>`;
      }
      if (resultado.salida) html += `<details class="salida-detalle"><summary>Lo que imprimió tu código</summary><pre class="salida-texto">${esc(resultado.salida)}</pre></details>`;
      resultadoEl.innerHTML = html;
      pintarAyudas();
      if (ok) lanzarConfeti();
      resultadoEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    $("#ejecutar", c).addEventListener("click", () => correr("ejecutar"));
    $("#comprobar", c).addEventListener("click", () => correr("probar"));
    $("#reiniciar", c).addEventListener("click", () => {
      if (confirm("¿Volver al código inicial? Perderás lo que escribiste.")) editor.setValue(e.inicial);
    });
    pintarAyudas();
    Py.precalentar();
    setTimeout(() => editor.refresh(), 0);
    return e.titulo;
  }

  function vistaEjercicioLocal(c, e, cabecera, pie) {
    const estado = Progreso.ejercicio(e.id);
    c.innerHTML = `${cabecera}
      <section class="tarjeta contenido enunciado">${Md.render(e.enunciado)}</section>
      <section class="tarjeta instrucciones-local">
        <h3>💻 Cómo trabajar este ejercicio</h3>
        <ol>
          <li>Abre la carpeta del curso en VS Code y activa tu entorno virtual.</li>
          <li>Tus archivos están en <code>ejercicios/${esc(e.id)}/</code>. Escribe tu solución ahí.</li>
          <li>Para comprobarla, ejecuta en la terminal de VS Code:</li>
        </ol>
        <pre><code class="language-bash">python comprobar.py ${esc(e.id)}</code></pre>
        <p class="texto-suave">El script cuenta tus intentos y te muestra las pistas y, al tercer fallo, la solución explicada. Los errores de sintaxis no cuentan como intento.</p>
        <div class="estado-local">
          <span>Estado en la página:</span>
          <button type="button" class="boton ${estado.estado === "resuelto" ? "boton-ok" : ""}" data-estado="resuelto">✅ Lo resolví</button>
          <button type="button" class="boton ${estado.estado === "solucion" ? "boton-repaso" : ""}" data-estado="solucion">📖 Lo resolví viendo la solución</button>
          <button type="button" class="boton boton-fantasma" data-estado="nuevo">Desmarcar</button>
        </div>
      </section>${pie}`;
    Md.activar(c);
    c.querySelectorAll("[data-estado]").forEach((b) =>
      b.addEventListener("click", () => {
        Progreso.actualizarEjercicio(e.id, { estado: b.dataset.estado, intentos: b.dataset.estado === "nuevo" ? 0 : estado.intentos || 0 });
        if (b.dataset.estado === "resuelto") lanzarConfeti();
        vistaEjercicio(c, e);
      })
    );
    return e.titulo;
  }

  // -------------------------------------------------------------------------
  // Vista: proyecto, referencia y repaso
  // -------------------------------------------------------------------------

  function vistaProyecto(c, p) {
    const nivel = NIVELES[p.nivel];
    const estado = Progreso.proyecto(p.id);
    const pp = progresoProyecto(p);
    c.classList.add("vista-lectura");
    let html = `${migas([{ texto: "Inicio", href: "#/" }, { texto: `Nivel ${nivel.nombre}` }, { texto: "Proyecto" }])}
      <header class="cabecera-modulo ${nivel.clase}">
        <div class="cabecera-icono">🏁</div>
        <div class="cabecera-texto">
          <div class="cabecera-etiqueta">${nivel.icono} Proyecto de cierre · Nivel ${nivel.nombre}</div>
          <h1>${esc(p.titulo)}</h1><p>${esc(p.resumen || "")}</p>
          <div class="cabecera-datos"><span>📁 <code>${esc(p.carpeta)}</code></span><span>⏱️ ${esc(p.duracion || "1 a 2 semanas")}</span></div>
        </div>
        <div class="cabecera-progreso">${anillo(pp.total ? (pp.marcados / pp.total) * 100 : 0, 84)}<span>${pp.marcados}/${pp.total}</span></div>
      </header>
      <article class="contenido">${Md.render(p.contenido)}</article>
      <section class="tarjeta criterios"><h2>✅ Lista de criterios</h2><p class="texto-suave">Revisa tu proyecto contra cada criterio. Marca solo lo que realmente cumples.</p>`;
    p.criterios.forEach((cr, i) => {
      html += `<label class="criterio"><input type="checkbox" data-i="${i}" ${estado.criterios?.[i] ? "checked" : ""}><span>${marked.parseInline(cr)}</span></label>`;
    });
    html += `<div class="quiz-pie"><button type="button" class="boton ${pp.terminado ? "boton-ok" : "boton-primario"}" id="terminar">${pp.terminado ? "🏆 Proyecto terminado" : "Marcar el proyecto como terminado"}</button><span id="aviso-proyecto" class="texto-suave"></span></div></section>`;
    c.innerHTML = html;
    Md.activar(c);
    c.querySelectorAll(".criterio input").forEach((caja) =>
      caja.addEventListener("change", () => {
        Progreso.marcarCriterio(p.id, caja.dataset.i, caja.checked);
        const nuevo = progresoProyecto(p);
        c.querySelector(".cabecera-progreso span").textContent = `${nuevo.marcados}/${nuevo.total}`;
      })
    );
    $("#terminar", c).addEventListener("click", () => {
      const actual = progresoProyecto(p);
      if (actual.terminado) return Progreso.estadoProyecto(p.id, "en_curso"), vistaProyecto(c, p);
      if (actual.marcados < actual.total) {
        $("#aviso-proyecto", c).textContent = `Te faltan ${actual.total - actual.marcados} criterios por cumplir.`;
        return;
      }
      Progreso.estadoProyecto(p.id, "terminado");
      lanzarConfeti();
      vistaProyecto(c, p);
    });
    return p.titulo;
  }

  function vistaReferencia(c, r) {
    c.classList.add("vista-lectura");
    c.innerHTML = `${migas([{ texto: "Inicio", href: "#/" }, { texto: "Referencia" }])}
      <header class="cabecera-leccion"><div class="cabecera-etiqueta">Referencia</div><h1>${esc(r.icono || "")} ${esc(r.titulo)}</h1></header>
      <article class="contenido">${Md.render(r.contenido)}</article>`;
    Md.activar(c);
    return r.titulo;
  }

  function vistaRepaso(c) {
    const lista = listaRepaso();
    let html = `${migas([{ texto: "Inicio", href: "#/" }, { texto: "Para repasar" }])}
      <header class="cabecera-leccion"><div class="cabecera-etiqueta">Lista de repaso</div><h1>🔁 Ejercicios para repasar</h1>
      <p>Aquí quedan los ejercicios que resolviste viendo la solución. Lo ideal es volver a intentarlos unos días después, sin mirar.</p></header>`;
    if (!lista.length) {
      html += `<div class="tarjeta vacio">🎉 No tienes ejercicios pendientes de repaso.</div>`;
    } else {
      html += `<div class="lista">${lista
        .map((e) => `<a class="fila estado-solucion" href="#/ejercicio/${e.id}"><span class="fila-numero">📖</span><span class="fila-texto"><b>${esc(e.titulo)}</b><small>Módulo ${e.modulo.numero}: ${esc(e.modulo.titulo)}</small></span><span class="fila-meta">${chipDificultad(e.dificultad)}${chipTipo(e.tipo)}</span></a>`)
        .join("")}</div>`;
    }
    c.innerHTML = html;
    return "Para repasar";
  }

  // -------------------------------------------------------------------------
  // Diálogo de progreso y efectos
  // -------------------------------------------------------------------------

  function abrirDialogoProgreso() {
    const dialogo = $("#dialogo-progreso");
    const d = Progreso.datos;
    $("#dialogo-progreso-info").textContent = d.actualizado ? `Última actualización: ${new Date(d.actualizado).toLocaleString("es")}` : "Todavía no hay progreso guardado.";
    dialogo.showModal();
  }

  function configurarDialogo() {
    const dialogo = $("#dialogo-progreso");
    $("#exportar").addEventListener("click", () => Progreso.exportar());
    $("#importar").addEventListener("change", async (ev) => {
      const archivo = ev.target.files[0];
      if (!archivo) return;
      try {
        Progreso.importar(await archivo.text());
        $("#dialogo-progreso-info").textContent = "✅ Progreso importado y combinado con el de este navegador.";
        enrutar();
      } catch (error) {
        $("#dialogo-progreso-info").textContent = "❌ " + error.message;
      }
      ev.target.value = "";
    });
    $("#borrar").addEventListener("click", () => {
      if (confirm("¿Borrar todo tu progreso en este navegador? Exporta antes una copia si la quieres conservar.")) {
        Progreso.borrarTodo();
        dialogo.close();
        enrutar();
      }
    });
    $("#cerrar-dialogo").addEventListener("click", () => dialogo.close());
  }

  function lanzarConfeti() {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const capa = document.createElement("div");
    capa.className = "confeti";
    const colores = ["#4f46e5", "#16a34a", "#f59e0b", "#ef4444", "#06b6d4", "#a855f7"];
    for (let i = 0; i < 70; i++) {
      const pieza = document.createElement("i");
      pieza.style.left = Math.random() * 100 + "vw";
      pieza.style.background = colores[i % colores.length];
      pieza.style.animationDelay = Math.random() * 0.4 + "s";
      pieza.style.animationDuration = 1.6 + Math.random() * 1.4 + "s";
      pieza.style.transform = `rotate(${Math.random() * 360}deg)`;
      capa.appendChild(pieza);
    }
    document.body.appendChild(capa);
    setTimeout(() => capa.remove(), 3500);
  }

  document.addEventListener("DOMContentLoaded", () => {
    configurarDialogo();
    iniciar();
  });

  return { indice: () => indice, curso: () => curso };
})();
