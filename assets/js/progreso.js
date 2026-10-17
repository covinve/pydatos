/* Progreso del estudiante: se guarda en el navegador (localStorage)
 * y se puede exportar/importar como archivo para sincronizar casa y oficina. */

const Progreso = (() => {
  const CLAVE = "pydatos.progreso.v1";
  const MAX_INTENTOS = 3;
  let datos = cargar();
  const oyentes = new Set();

  function vacio() {
    return { version: 1, lecciones: {}, ejercicios: {}, proyectos: {}, actividad: [], ultimo: null, actualizado: null };
  }

  function cargar() {
    try {
      const texto = localStorage.getItem(CLAVE);
      if (!texto) return vacio();
      return { ...vacio(), ...JSON.parse(texto) };
    } catch {
      return vacio();
    }
  }

  function guardar() {
    datos.actualizado = new Date().toISOString();
    try {
      localStorage.setItem(CLAVE, JSON.stringify(datos));
    } catch {
      /* almacenamiento lleno o bloqueado: el curso sigue funcionando */
    }
    oyentes.forEach((f) => f());
  }

  function hoy() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function registrarActividad() {
    const dia = hoy();
    if (!datos.actividad.includes(dia)) {
      datos.actividad.push(dia);
      datos.actividad.sort();
    }
  }

  // --- Lecciones ---------------------------------------------------------

  function leccion(id) {
    return datos.lecciones[id] || null;
  }

  function completarLeccion(id, quiz) {
    const previo = datos.lecciones[id] || {};
    datos.lecciones[id] = { ...previo, completada: true, fecha: previo.fecha || hoy(), ...(quiz ? { quiz } : {}) };
    registrarActividad();
    guardar();
  }

  // --- Ejercicios ----------------------------------------------------------

  function ejercicio(id) {
    return datos.ejercicios[id] || { estado: "nuevo", intentos: 0 };
  }

  function actualizarEjercicio(id, cambios, contarActividad = true) {
    datos.ejercicios[id] = { ...ejercicio(id), ...cambios };
    if (contarActividad) registrarActividad();
    guardar();
    return datos.ejercicios[id];
  }

  function guardarCodigo(id, codigo) {
    const e = ejercicio(id);
    datos.ejercicios[id] = { ...e, codigo, estado: e.estado === "nuevo" ? "en_curso" : e.estado };
    guardar();
  }

  /** Registra un intento fallido. Devuelve el estado actualizado. */
  function intentoFallido(id) {
    const e = ejercicio(id);
    const intentos = (e.intentos || 0) + 1;
    let estado = e.estado === "resuelto" ? "resuelto" : "en_curso";
    if (intentos >= MAX_INTENTOS && e.estado !== "resuelto") estado = "solucion";
    if (e.estado === "solucion") estado = "solucion";
    return actualizarEjercicio(id, { intentos, estado });
  }

  function resuelto(id) {
    const e = ejercicio(id);
    const cambios = { estado: "resuelto", fecha: hoy() };
    if (e.estado === "solucion") cambios.repasado = true;
    return actualizarEjercicio(id, cambios);
  }

  /** Vuelve a empezar un ejercicio (para repasarlo sin ayudas). */
  function reiniciarEjercicio(id) {
    const e = ejercicio(id);
    return actualizarEjercicio(id, { intentos: 0, codigo: null, reintento: true, estado: e.estado === "resuelto" ? "resuelto" : e.estado }, false);
  }

  // --- Proyectos -------------------------------------------------------------

  function proyecto(id) {
    return datos.proyectos[id] || { criterios: {}, estado: "nuevo" };
  }

  function marcarCriterio(id, indice, valor) {
    const p = proyecto(id);
    p.criterios = { ...p.criterios, [indice]: valor };
    if (p.estado === "nuevo") p.estado = "en_curso";
    datos.proyectos[id] = p;
    registrarActividad();
    guardar();
  }

  function estadoProyecto(id, estado) {
    datos.proyectos[id] = { ...proyecto(id), estado };
    registrarActividad();
    guardar();
  }

  // --- Navegación, racha y exportación -------------------------------------------

  function recordarUltimo(ruta) {
    if (datos.ultimo !== ruta) {
      datos.ultimo = ruta;
      try {
        localStorage.setItem(CLAVE, JSON.stringify(datos));
      } catch {
        /* sin almacenamiento */
      }
    }
  }

  function racha() {
    const dias = new Set(datos.actividad);
    const fecha = new Date();
    const formato = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    if (!dias.has(formato(fecha))) fecha.setDate(fecha.getDate() - 1); // la racha sigue viva si estudiaste ayer
    let cuenta = 0;
    while (dias.has(formato(fecha))) {
      cuenta++;
      fecha.setDate(fecha.getDate() - 1);
    }
    return cuenta;
  }

  function exportar() {
    const blob = new Blob([JSON.stringify(datos, null, 2)], { type: "application/json" });
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(blob);
    enlace.download = "progreso-pydatos.json";
    enlace.click();
    setTimeout(() => URL.revokeObjectURL(enlace.href), 1000);
  }

  /** Importa un archivo de progreso. Combina: conserva lo más avanzado de cada lado. */
  function importar(texto) {
    const otro = JSON.parse(texto);
    if (!otro || otro.version !== 1) throw new Error("El archivo no es un progreso válido de PyDatos");
    const rango = { nuevo: 0, en_curso: 1, solucion: 2, resuelto: 3 };
    for (const [id, l] of Object.entries(otro.lecciones || {})) {
      if (!datos.lecciones[id] || !datos.lecciones[id].completada) datos.lecciones[id] = l;
    }
    for (const [id, e] of Object.entries(otro.ejercicios || {})) {
      const mio = datos.ejercicios[id];
      if (!mio || (rango[e.estado] || 0) > (rango[mio.estado] || 0)) datos.ejercicios[id] = e;
      else if (mio && !mio.codigo && e.codigo) mio.codigo = e.codigo;
    }
    for (const [id, p] of Object.entries(otro.proyectos || {})) {
      const mio = datos.proyectos[id];
      datos.proyectos[id] = mio ? { ...p, ...mio, criterios: { ...p.criterios, ...mio.criterios } } : p;
    }
    datos.actividad = [...new Set([...(datos.actividad || []), ...(otro.actividad || [])])].sort();
    guardar();
  }

  function borrarTodo() {
    datos = vacio();
    guardar();
  }

  return {
    MAX_INTENTOS,
    get datos() {
      return datos;
    },
    leccion,
    completarLeccion,
    ejercicio,
    actualizarEjercicio,
    guardarCodigo,
    intentoFallido,
    resuelto,
    reiniciarEjercicio,
    proyecto,
    marcarCriterio,
    estadoProyecto,
    recordarUltimo,
    racha,
    exportar,
    importar,
    borrarTodo,
    alCambiar: (f) => oyentes.add(f),
  };
})();
