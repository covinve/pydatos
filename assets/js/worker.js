/* Web Worker que ejecuta Python con Pyodide.
 * Corre aparte de la página para que un bucle infinito no la congele:
 * si algo tarda demasiado, la página termina este worker y crea otro. */

import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

let listo = null;
// Si pandas se importa antes de que pyarrow esté instalado, pandas guarda que "no hay Arrow" y luego
// falla al escribir Parquet o al convertir desde Polars/DuckDB. En ese caso hay que empezar de cero.
const USA_ARROW = /\b(pyarrow|polars|duckdb)\b|parquet/;
let pandasSinArrow = false;

async function iniciar() {
  const pyodide = await loadPyodide({ indexURL: PYODIDE_URL });
  const respuesta = await fetch(new URL("../py/evaluador.py", import.meta.url), { cache: "no-cache" });
  const fuente = await respuesta.text();
  pyodide.FS.mkdirTree("/home/pyodide/lib");
  pyodide.FS.writeFile("/home/pyodide/lib/evaluador.py", fuente);
  pyodide.FS.mkdirTree("/trabajo");
  pyodide.runPython(`
import sys, os
sys.path.insert(0, "/home/pyodide/lib")
os.chdir("/trabajo")
import evaluador
`);
  return pyodide;
}

function escribirArchivos(pyodide, archivos) {
  for (const [ruta, datos] of Object.entries(archivos || {})) {
    const completa = "/trabajo/" + ruta;
    const carpeta = completa.slice(0, completa.lastIndexOf("/"));
    pyodide.FS.mkdirTree(carpeta);
    pyodide.FS.writeFile(completa, new Uint8Array(datos));
  }
}

self.onmessage = async (evento) => {
  const { id, tipo, codigo = "", pruebas = "", preparacion = "", archivos } = evento.data;
  try {
    if (!listo) {
      self.postMessage({ id, estado: "cargando", texto: "Cargando Python…" });
      listo = iniciar();
    }
    const pyodide = await listo;
    let todo = [codigo, pruebas, preparacion].join("\n");
    // correr_pytest (del evaluador) usa pytest aunque el código no lo importe
    if (todo.includes("correr_pytest")) todo += "\nimport pytest\n";
    // pandas usa scipy para las correlaciones de Spearman y Kendall
    if (/spearman|kendall/.test(todo)) todo += "\nimport scipy\n";
    if (USA_ARROW.test(todo)) {
      if (pandasSinArrow) {
        self.postMessage({ id, estado: "reiniciar" });
        return;
      }
      todo += "\nimport pyarrow\n";
    }
    await pyodide.loadPackagesFromImports(todo, {
      messageCallback: (texto) => {
        const paquete = /Loading (.+)/.exec(texto);
        if (paquete) self.postMessage({ id, estado: "cargando", texto: "Cargando librerías: " + paquete[1] });
      },
      errorCallback: () => {},
    });
    if (pyodide.loadedPackages.pandas && !pyodide.loadedPackages.pyarrow) pandasSinArrow = true;
    if (tipo === "preparar") {
      self.postMessage({ id, estado: "listo", resultado: {} });
      return;
    }
    escribirArchivos(pyodide, archivos);
    self.postMessage({ id, estado: "ejecutando" });

    const evaluador = pyodide.pyimport("evaluador");
    let salida;
    if (tipo === "trazar") {
      salida = evaluador.trazar(codigo);
    } else {
      salida = evaluador.ejecutar(codigo, tipo === "probar" ? "probar" : "ejecutar", pruebas, preparacion);
    }
    const resultado = salida.toJs({ dict_converter: Object.fromEntries, create_pyproxies: false });
    salida.destroy();
    self.postMessage({ id, estado: "listo", resultado });
  } catch (error) {
    self.postMessage({ id, estado: "fallo", texto: String(error && error.message ? error.message : error) });
  }
};
