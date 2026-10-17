/* Puente entre la página y el worker de Python.
 * Py.ejecutar({...}) devuelve una promesa con el resultado.
 * Las peticiones se atienden de una en una. */

const Py = (() => {
  let worker = null;
  let siguienteId = 1;
  let actual = null;
  const cola = [];
  const cacheArchivos = new Map();
  const oyentes = new Set();
  let estadoGlobal = "apagado"; // apagado | cargando | listo

  function avisar(estado, texto) {
    estadoGlobal = estado;
    oyentes.forEach((f) => f(estado, texto));
  }

  function crearWorker() {
    // La versión en la URL evita que el navegador use un worker viejo después de actualizar el sitio.
    worker = new Worker("assets/js/worker.js?v=2026-10-17b", { type: "module" });
    worker.onmessage = (evento) => {
      const mensaje = evento.data;
      if (!actual || mensaje.id !== actual.id) return;
      if (mensaje.estado === "cargando") {
        avisar("cargando", mensaje.texto);
        actual.alAvanzar && actual.alAvanzar(mensaje.texto);
      } else if (mensaje.estado === "ejecutando") {
        avisar("listo");
        actual.alAvanzar && actual.alAvanzar("Ejecutando…");
        iniciarTemporizador();
      } else if (mensaje.estado === "listo") {
        avisar("listo");
        terminar({ ok: true, ...mensaje.resultado });
      } else if (mensaje.estado === "fallo") {
        terminar({ ok: false, error: "Error interno: " + mensaje.texto });
      }
    };
    worker.onerror = (e) => {
      if (actual) terminar({ ok: false, error: "No se pudo iniciar Python: " + (e.message || "revisa tu conexión a internet") });
    };
  }

  function iniciarTemporizador() {
    const tarea = actual;
    tarea.temporizador = setTimeout(() => {
      if (actual !== tarea) return;
      worker.terminate();
      worker = null;
      avisar("apagado");
      terminar({
        ok: true,
        tiempoAgotado: true,
        error: `Tiempo agotado: tu código tardó más de ${tarea.timeout / 1000} segundos. ¿Hay un bucle infinito?`,
        salida: "",
        pruebas: [],
        figuras: [],
      });
    }, tarea.timeout);
  }

  function terminar(resultado) {
    const tarea = actual;
    actual = null;
    if (tarea) {
      clearTimeout(tarea.temporizador);
      tarea.resolver(resultado);
    }
    procesar();
  }

  async function leerArchivos(rutas) {
    const archivos = {};
    for (const ruta of rutas || []) {
      if (!cacheArchivos.has(ruta)) {
        const respuesta = await fetch("contenido/datos/" + ruta);
        if (!respuesta.ok) throw new Error("No se encontró el archivo de datos " + ruta);
        cacheArchivos.set(ruta, await respuesta.arrayBuffer());
      }
      // El nombre dentro de Python es solo el nombre del archivo: "muestra/cdr.csv" -> "cdr.csv"
      const nombre = ruta.split("/").pop();
      archivos[nombre] = cacheArchivos.get(ruta).slice(0);
    }
    return archivos;
  }

  async function procesar() {
    if (actual || cola.length === 0) return;
    actual = cola.shift();
    if (!worker) crearWorker();
    try {
      const archivos = await leerArchivos(actual.archivos);
      worker.postMessage({
        id: actual.id,
        tipo: actual.tipo,
        codigo: actual.codigo,
        pruebas: actual.pruebas,
        preparacion: actual.preparacion,
        archivos,
      });
    } catch (error) {
      terminar({ ok: false, error: String(error.message || error) });
    }
  }

  function ejecutar(opciones) {
    return new Promise((resolver) => {
      cola.push({
        id: siguienteId++,
        tipo: opciones.tipo || "ejecutar",
        codigo: opciones.codigo || "",
        pruebas: opciones.pruebas || "",
        preparacion: opciones.preparacion || "",
        archivos: opciones.archivos || [],
        timeout: opciones.timeout || 20000,
        alAvanzar: opciones.alAvanzar,
        resolver,
      });
      procesar();
    });
  }

  /** Carga Python en segundo plano para que la primera ejecución sea rápida. */
  function precalentar() {
    if (estadoGlobal === "apagado" && !actual && cola.length === 0) {
      ejecutar({ tipo: "preparar" });
    }
  }

  return {
    ejecutar,
    precalentar,
    alCambiarEstado: (f) => oyentes.add(f),
    get estado() {
      return estadoGlobal;
    },
  };
})();
