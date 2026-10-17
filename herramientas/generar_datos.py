"""Generador de datos sintéticos de facturación telco para el curso PyDatos.

Crea datos FALSOS pero realistas (planes, clientes, CDR y facturas) con errores
sembrados a propósito, y un archivo `esperado.json` con los resultados correctos
para que puedas comprobar tus programas.

Con la misma semilla siempre obtienes los mismos datos.

Ejemplos (desde la carpeta del curso, con el entorno virtual activo):
    python herramientas/generar_datos.py --tamano 10MB
    python herramientas/generar_datos.py --tamano 1GB --formato ambos
    python herramientas/generar_datos.py --tamano 20GB
    python herramientas/generar_datos.py --filas 5000 --salida contenido/datos/muestra

Los archivos quedan en datos/<tamaño>/ (esa carpeta no se sube a Git).
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

RAIZ = Path(__file__).resolve().parent.parent
PERIODO = "202609"
DIAS_PERIODO = 30
IVA = 0.19
BYTES_POR_FILA_CSV = 70  # promedio aproximado de una fila de cdr.csv
FILAS_POR_LOTE = 1_000_000
CDR_POR_CLIENTE = 470  # consumo promedio mensual de una línea

TAMANOS = {"10MB": 10e6, "100MB": 100e6, "1GB": 1e9, "5GB": 5e9, "20GB": 20e9}

# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------

PLANES = pd.DataFrame(
    [
        # plan_id, nombre, segmento, cargo_fijo, min, mb, sms, tarifa_min, tarifa_int, tarifa_mb, tarifa_sms
        ("BAS10", "Plan Básico 10", "RESIDENCIAL", 19900, 100, 5120, 50, 150, 1100, 22, 70),
        ("HOG30", "Plan Hogar 30", "RESIDENCIAL", 35900, 300, 15360, 100, 120, 950, 18, 60),
        ("HOG60", "Plan Hogar 60", "RESIDENCIAL", 55900, 600, 40960, 200, 110, 900, 15, 55),
        ("ILIM", "Plan Ilimitado", "RESIDENCIAL", 89900, -1, -1, -1, 0, 850, 0, 0),
        ("EMP100", "Empresarial 100", "EMPRESARIAL", 79900, 1000, 51200, 500, 100, 800, 12, 50),
        ("EMP300", "Empresarial 300", "EMPRESARIAL", 149900, 3000, 153600, 1000, 90, 750, 10, 45),
    ],
    columns=[
        "plan_id", "nombre", "segmento", "cargo_fijo", "minutos_incluidos", "mb_incluidos",
        "sms_incluidos", "tarifa_minuto", "tarifa_minuto_internacional", "tarifa_mb", "tarifa_sms",
    ],
)
PROB_PLAN_RESIDENCIAL = [0.18, 0.34, 0.30, 0.18]
PROB_PLAN_EMPRESARIAL = [0.62, 0.38]

NOMBRES = [
    "Andrés", "María", "José", "Lucía", "Camilo", "Valentina", "Julián", "Sofía", "Óscar", "Mónica",
    "Sebastián", "Ángela", "Iván", "Natalia", "Martín", "Daniela", "Hernán", "Paula", "Germán", "Inés",
    "Felipe", "Juliana", "Ramón", "Carolina", "Tomás", "Verónica", "Raúl", "Catalina", "Néstor", "Lorena",
]
APELLIDOS = [
    "Gómez", "Rodríguez", "Martínez", "López", "García", "Pérez", "Hernández", "Sánchez", "Ramírez", "Díaz",
    "Muñoz", "Castaño", "Peña", "Ibáñez", "Núñez", "Ortiz", "Jiménez", "Vargas", "Rojas", "Suárez",
    "Patiño", "Montaño", "Quiñones", "Álvarez", "Beltrán", "Acuña", "Cárdenas", "Londoño", "Zúñiga", "Mejía",
]
EMPRESA_A = ["Distribuciones", "Comercializadora", "Inversiones", "Transportes", "Servicios", "Construcciones", "Logística", "Alimentos", "Tecnología", "Farmacéutica"]
EMPRESA_B = ["Andina", "del Caribe", "Pacífico", "Nogal", "Montaña", "Río Claro", "Sabana", "La Ceiba", "Cóndor", "Guayacán"]
EMPRESA_C = ["S.A.S.", "S.A.", "Ltda.", "& Cía."]
CIUDADES = [
    ("Bogotá", "ANDINA", 0.30), ("Medellín", "ANDINA", 0.16), ("Cali", "PACÍFICO", 0.12),
    ("Barranquilla", "CARIBE", 0.09), ("Cartagena", "CARIBE", 0.06), ("Bucaramanga", "ANDINA", 0.06),
    ("Pereira", "ANDINA", 0.05), ("Cúcuta", "ANDINA", 0.05), ("Ibagué", "ANDINA", 0.04),
    ("Santa Marta", "CARIBE", 0.03), ("Villavicencio", "ORINOQUÍA", 0.03), ("Pasto", "PACÍFICO", 0.01),
]

ERRORES = ["duplicado", "duracion_negativa", "fecha_invalida", "linea_vacia", "linea_desconocida", "tipo_desconocido"]
TASA_ERROR = {"duracion_negativa": 0.0006, "fecha_invalida": 0.0005, "linea_vacia": 0.0004, "linea_desconocida": 0.0005, "tipo_desconocido": 0.0003}
TASA_DUPLICADO = 0.002
# Código numérico de cada error (posición en ERRORES)
E_DURACION, E_FECHA, E_VACIA, E_DESCONOCIDA, E_TIPO = 1, 2, 3, 4, 5

TIPOS = np.array(["VOZ", "SMS", "DATOS"])
TIPOS_TEXTO = ["VOZ", "SMS", "DATOS", "VOX", "MMS", "DAT"]  # los tres últimos son errores sembrados
DESTINOS = np.array(["LOCAL", "NACIONAL", "INTERNACIONAL", ""])

# Diseño del archivo de ancho fijo: (campo, inicio, longitud). Posiciones desde 1.
DISENO_ANCHO_FIJO = [
    ("cdr_id", 1, 12), ("linea_origen", 13, 10), ("linea_destino", 23, 13), ("tipo", 36, 5),
    ("destino", 41, 13), ("fecha_inicio", 54, 14), ("duracion_seg", 68, 6), ("mb", 74, 10), ("celda", 84, 8),
]
ANCHO_REGISTRO = 91


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

def generar_clientes(n: int, rng: np.random.Generator) -> pd.DataFrame:
    empresarial = rng.random(n) < 0.18
    plan = np.where(
        empresarial,
        rng.choice(PLANES.plan_id[4:].to_numpy(), n, p=PROB_PLAN_EMPRESARIAL),
        rng.choice(PLANES.plan_id[:4].to_numpy(), n, p=PROB_PLAN_RESIDENCIAL),
    )
    nombres = np.array([f"{a} {b} {c}" for a, b, c in zip(rng.choice(NOMBRES, n), rng.choice(APELLIDOS, n), rng.choice(APELLIDOS, n))], dtype=object)
    empresas = np.array([f"{a} {b} {c}" for a, b, c in zip(rng.choice(EMPRESA_A, n), rng.choice(EMPRESA_B, n), rng.choice(EMPRESA_C, n))], dtype=object)
    probs = np.array([c[2] for c in CIUDADES])
    ciudad_idx = rng.choice(len(CIUDADES), n, p=probs / probs.sum())
    # Números de línea únicos que empiezan por 300-350
    lineas = 3_000_000_000 + rng.choice(500_000_000, n, replace=False)
    dias_alta = rng.integers(0, 365 * 12, n)  # hasta 12 años de antigüedad
    fecha_alta = np.datetime64("2026-09-01") - dias_alta.astype("timedelta64[D]")
    estado = np.where(rng.random(n) < 0.05, "SUSPENDIDO", "ACTIVO")
    documento = np.where(empresarial, rng.integers(800_000_000, 999_999_999, n), rng.integers(10_000_000, 1_299_999_999, n))
    return pd.DataFrame(
        {
            "cliente_id": [f"CL{i:07d}" for i in range(1, n + 1)],
            "nombre": np.where(empresarial, empresas, nombres),
            "tipo_documento": np.where(empresarial, "NIT", np.where(rng.random(n) < 0.04, "CE", "CC")),
            "documento": documento,
            "segmento": np.where(empresarial, "EMPRESARIAL", "RESIDENCIAL"),
            "ciudad": [CIUDADES[i][0] for i in ciudad_idx],
            "region": [CIUDADES[i][1] for i in ciudad_idx],
            "plan_id": plan,
            "linea": lineas.astype(np.int64),
            "fecha_alta": np.datetime_as_string(fecha_alta, unit="D"),
            "estado": estado,
        }
    )


# ---------------------------------------------------------------------------
# CDR
# ---------------------------------------------------------------------------

class Acumulador:
    """Suma, por cliente, el consumo de los CDR válidos (para las facturas y esperado.json)."""

    def __init__(self, n_clientes: int):
        self.min_nac = np.zeros(n_clientes, np.int64)
        self.min_int = np.zeros(n_clientes, np.int64)
        self.milli_mb = np.zeros(n_clientes, np.int64)
        self.sms = np.zeros(n_clientes, np.int64)
        self.cdr_validos = np.zeros(n_clientes, np.int64)
        self.errores = {e: 0 for e in ERRORES}
        self.por_tipo = {"VOZ": 0, "SMS": 0, "DATOS": 0}
        self.total = 0
        self.por_dia = np.zeros(DIAS_PERIODO, np.int64)
        self.por_hora_voz = np.zeros(24, np.int64)


def generar_lote(inicio_id: int, n: int, clientes: pd.DataFrame, pesos_acum: np.ndarray, activos: np.ndarray,
                 rng: np.random.Generator, acum: Acumulador) -> pa.Table:
    n_clientes = len(clientes)
    cliente = activos[np.searchsorted(pesos_acum, rng.random(n) * pesos_acum[-1])]
    tipo = rng.choice(3, n, p=[0.30, 0.05, 0.65])
    destino = np.where(tipo == 2, 3, rng.choice(3, n, p=[0.55, 0.42, 0.03]))
    destino = np.where((tipo == 1) & (destino == 2), 1, destino)  # SMS: sin internacional
    duracion = np.where(tipo == 0, np.clip(rng.lognormal(4.3, 1.0, n), 0, 7200).astype(np.int64), 0)
    duracion = np.where((tipo == 0) & (rng.random(n) < 0.06), 0, duracion)  # llamadas no contestadas
    duracion = np.where(tipo == 2, rng.integers(10, 3600, n), duracion)
    milli_mb = np.where(tipo == 2, np.clip(rng.lognormal(3.2, 1.2, n) * 1000, 1, 4_000_000).astype(np.int64), 0)
    segundos = rng.integers(0, DIAS_PERIODO * 86400, n)
    # Más tráfico de día que de madrugada
    hora = (segundos % 86400) // 3600
    noche = (hora < 6) & (rng.random(n) < 0.7)
    segundos = np.where(noche, segundos + 8 * 3600, segundos) % (DIAS_PERIODO * 86400)
    lineas = clientes.linea.to_numpy()
    linea_origen = lineas[cliente]
    linea_destino = np.where(destino == 2, 10_000_000_000 + rng.integers(0, 9_999_999_999, n),
                             np.where(destino == 0, 6_010_000_000 + rng.integers(0, 9_999_999, n), 3_000_000_000 + rng.integers(0, 500_000_000, n)))
    linea_destino = np.where(tipo == 2, 0, linea_destino)
    celda = rng.integers(10000, 99999, n)
    ids = np.arange(inicio_id, inicio_id + n, dtype=np.int64)

    # --- errores sembrados: cada fila con error tiene exactamente uno ---
    sorteo = rng.random(n)
    error = np.full(n, -1)
    limite = 0.0
    for codigo, nombre in enumerate(ERRORES[1:], start=1):
        tasa = TASA_ERROR[nombre]
        elegidos = (sorteo >= limite) & (sorteo < limite + tasa)
        if nombre == "duracion_negativa":
            elegidos &= tipo == 0
        error[elegidos] = codigo
        limite += tasa
    valido = error == -1

    # Acumular consumo válido por cliente
    voz = valido & (tipo == 0)
    minutos = (duracion + 59) // 60
    acum.min_nac += np.bincount(cliente[voz & (destino < 2)], weights=minutos[voz & (destino < 2)], minlength=n_clientes).astype(np.int64)
    acum.min_int += np.bincount(cliente[voz & (destino == 2)], weights=minutos[voz & (destino == 2)], minlength=n_clientes).astype(np.int64)
    datos = valido & (tipo == 2)
    acum.milli_mb += np.bincount(cliente[datos], weights=milli_mb[datos], minlength=n_clientes).astype(np.int64)
    acum.sms += np.bincount(cliente[valido & (tipo == 1)], minlength=n_clientes)
    acum.cdr_validos += np.bincount(cliente[valido], minlength=n_clientes)
    for t, nombre in enumerate(TIPOS):
        acum.por_tipo[nombre] += int(np.sum(valido & (tipo == t)))
    acum.por_dia += np.bincount(segundos[valido] // 86400, minlength=DIAS_PERIODO)
    acum.por_hora_voz += np.bincount(((segundos % 86400) // 3600)[voz], minlength=24)
    for codigo, nombre in enumerate(ERRORES[1:], start=1):
        acum.errores[nombre] += int(np.sum(error == codigo))

    # --- columnas de texto (con pyarrow, que es mucho más rápido que pandas para esto) ---
    def texto(numeros):
        return pc.cast(pa.array(numeros), pa.string())

    def dos(numeros):
        return pc.utf8_lpad(texto(numeros), width=2, padding="0")

    dia, resto = segundos // 86400 + 1, segundos % 86400
    fecha = pc.binary_join_element_wise("2026-09-", dos(dia), " ", dos(resto // 3600), ":", dos(resto % 3600 // 60), ":", dos(resto % 60), "")
    malas = error == E_FECHA
    opciones_malas = np.array(["2026-09-31 10:15:00", "2026-13-02 08:00:00", "2026-09-00 12:30:00", "2026-09-10 14:61:00", "2026-09-15 25:10:00"])
    fecha = pc.if_else(pa.array(malas), pa.array(opciones_malas[rng.integers(0, len(opciones_malas), n)]), fecha)
    duracion_final = np.where(error == E_DURACION, -rng.integers(1, 600, n), duracion)
    origen_final = np.where(error == E_DESCONOCIDA, 3_990_000_000 + rng.integers(0, 9_999_999, n), linea_origen)
    origen = pc.if_else(pa.array(error == E_VACIA), "", texto(origen_final))
    tipo_final = np.where(error == E_TIPO, 3 + rng.integers(0, 3, n), tipo)
    destino_num = pc.if_else(pa.array(destino == 2), pc.binary_join_element_wise("00", texto(linea_destino), ""), texto(linea_destino))
    destino_num = pc.if_else(pa.array(tipo == 2), "", destino_num)

    lote = pa.table(
        {
            "cdr_id": pa.array(ids),
            "linea_origen": origen,
            "linea_destino": destino_num,
            "tipo": pa.array(TIPOS_TEXTO).take(pa.array(tipo_final)),
            "destino": pa.array(DESTINOS).take(pa.array(destino)),
            "fecha_inicio": fecha,
            "duracion_seg": pa.array(duracion_final),
            "mb_entero": pa.array(milli_mb // 1000),
            "mb_milesimas": pa.array(milli_mb % 1000),
            "celda": pc.binary_join_element_wise("CEL", texto(celda), ""),
        }
    )

    # --- duplicados: copias exactas de filas válidas, unas filas más adelante ---
    n_dup = int(round(n * TASA_DUPLICADO))
    if n_dup:
        origen_dup = rng.choice(np.flatnonzero(valido), n_dup, replace=False)
        claves = np.concatenate([np.arange(n, dtype=float), origen_dup + rng.integers(1, 5000, n_dup) + 0.5])
        indices = np.concatenate([np.arange(n), origen_dup])[np.argsort(claves, kind="stable")]
        lote = lote.take(pa.array(indices))
        acum.errores["duplicado"] += n_dup
    acum.total += lote.num_rows
    return lote


def tabla_csv(lote: pa.Table) -> pa.Table:
    mb = pc.binary_join_element_wise(
        pc.cast(lote["mb_entero"], pa.string()), pc.utf8_lpad(pc.cast(lote["mb_milesimas"], pa.string()), width=3, padding="0"), "."
    )
    columnas = ["cdr_id", "linea_origen", "linea_destino", "tipo", "destino", "fecha_inicio", "duracion_seg"]
    return pa.table({**{c: lote[c] for c in columnas}, "mb": mb, "celda": lote["celda"]})


def tabla_ancho_fijo(lote: pa.Table) -> pa.Table:
    def izquierda(col, ancho):
        return pc.utf8_rpad(col, width=ancho, padding=" ")

    def ceros(col, ancho):
        return pc.utf8_lpad(pc.cast(col, pa.string()), width=ancho, padding="0")

    fecha = pc.replace_substring_regex(lote["fecha_inicio"], pattern="[-: ]", replacement="")
    duracion = lote["duracion_seg"]
    negativa = pc.less(duracion, 0)
    duracion_txt = pc.if_else(negativa, pc.binary_join_element_wise("-", ceros(pc.negate(duracion), 5), ""), ceros(duracion, 6))
    mb = pc.binary_join_element_wise(ceros(lote["mb_entero"], 6), ceros(lote["mb_milesimas"], 3), ".")
    registro = pc.binary_join_element_wise(
        ceros(lote["cdr_id"], 12), izquierda(lote["linea_origen"], 10), izquierda(lote["linea_destino"], 13),
        izquierda(lote["tipo"], 5), izquierda(lote["destino"], 13), izquierda(fecha, 14), duracion_txt, mb,
        izquierda(lote["celda"], 8), "",
    )
    return pa.table({"registro": registro})


# ---------------------------------------------------------------------------
# Facturas
# ---------------------------------------------------------------------------

def redondear(valores: np.ndarray) -> np.ndarray:
    """Redondeo comercial (0.5 hacia arriba) a pesos enteros."""
    return np.floor(valores + 0.5).astype(np.int64)


def calcular_facturas(clientes: pd.DataFrame, acum: Acumulador) -> pd.DataFrame:
    planes = PLANES.set_index("plan_id")
    p = planes.loc[clientes.plan_id]
    mb_fact = (acum.milli_mb + 999) // 1000
    incl_min = p.minutos_incluidos.to_numpy()
    incl_mb = p.mb_incluidos.to_numpy()
    incl_sms = p.sms_incluidos.to_numpy()
    valor_voz = np.where(incl_min < 0, 0, np.maximum(0, acum.min_nac - incl_min) * p.tarifa_minuto.to_numpy())
    valor_int = acum.min_int * p.tarifa_minuto_internacional.to_numpy()
    valor_datos = np.where(incl_mb < 0, 0, np.maximum(0, mb_fact - incl_mb) * p.tarifa_mb.to_numpy())
    valor_sms = np.where(incl_sms < 0, 0, np.maximum(0, acum.sms - incl_sms) * p.tarifa_sms.to_numpy())
    cargo = p.cargo_fijo.to_numpy()
    antiguo = clientes.fecha_alta.to_numpy() < "2023-09-01"
    descuento = np.where((clientes.segmento.to_numpy() == "EMPRESARIAL") & antiguo, redondear(cargo * 0.10), 0)
    adicional = valor_voz + valor_int + valor_datos + valor_sms
    subtotal = cargo + adicional - descuento
    iva = redondear(subtotal * IVA)
    return pd.DataFrame(
        {
            "factura_id": [f"F{PERIODO}{i:07d}" for i in range(1, len(clientes) + 1)],
            "cliente_id": clientes.cliente_id,
            "linea": clientes.linea,
            "periodo": PERIODO,
            "plan_id": clientes.plan_id,
            "cargo_fijo": cargo,
            "valor_voz": valor_voz,
            "valor_internacional": valor_int,
            "valor_datos": valor_datos,
            "valor_sms": valor_sms,
            "consumo_adicional": adicional,
            "descuento": descuento,
            "subtotal": subtotal,
            "iva": iva,
            "total": subtotal + iva,
            "fecha_emision": "2026-10-05",
            "estado_pago": "PENDIENTE",
        }
    )


def sembrar_errores_factura(facturas: pd.DataFrame, rng: np.random.Generator) -> tuple[pd.DataFrame, dict]:
    """Simula errores del sistema de facturación: cobros distintos al consumo real."""
    emitidas = facturas.copy()
    n = len(emitidas)
    con_dif = rng.choice(n, max(1, int(n * 0.015)), replace=False)
    tipo = rng.choice(3, len(con_dif))
    for i, t in zip(con_dif, tipo):
        if t == 0:  # tarificación de datos inflada
            emitidas.loc[i, "valor_datos"] = emitidas.loc[i, "valor_datos"] + int(rng.integers(2, 60)) * 1000
        elif t == 1:  # no se aplicó el descuento / se cobró voz sin descontar el plan
            emitidas.loc[i, "valor_voz"] = emitidas.loc[i, "valor_voz"] + int(rng.integers(5, 120)) * 110
        else:  # se dejó de cobrar el consumo internacional
            emitidas.loc[i, "valor_internacional"] = 0 if emitidas.loc[i, "valor_internacional"] else emitidas.loc[i, "valor_internacional"] + 950
    filas = emitidas.index[con_dif]
    emitidas.loc[filas, "consumo_adicional"] = emitidas.loc[filas, ["valor_voz", "valor_internacional", "valor_datos", "valor_sms"]].sum(axis=1)
    emitidas.loc[filas, "subtotal"] = emitidas.loc[filas, "cargo_fijo"] + emitidas.loc[filas, "consumo_adicional"] - emitidas.loc[filas, "descuento"]
    emitidas.loc[filas, "iva"] = redondear(emitidas.loc[filas, "subtotal"].to_numpy() * IVA)
    emitidas.loc[filas, "total"] = emitidas.loc[filas, "subtotal"] + emitidas.loc[filas, "iva"]
    # Inconsistencias internas: el total no es subtotal + IVA
    disponibles = np.setdiff1d(np.arange(n), con_dif)
    inconsistentes = rng.choice(disponibles, max(1, int(n * 0.003)), replace=False)
    emitidas.loc[inconsistentes, "total"] = emitidas.loc[inconsistentes, "total"] + rng.integers(1, 50, len(inconsistentes)) * 100
    diferencia = (emitidas.total - facturas.total).to_numpy()
    resumen = {
        "facturas_con_diferencia_consumo": int(len(con_dif)),
        "facturas_inconsistentes": int(len(inconsistentes)),
        "facturas_total_distinto": int(np.sum(diferencia != 0)),
        "diferencia_total": int(diferencia.sum()),
        "diferencia_por_consumo": int(diferencia[con_dif].sum()),
    }
    return emitidas, resumen


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def generar(filas_objetivo: int, salida: Path, formato: str, semilla: int, etiqueta: str) -> dict:
    rng = np.random.default_rng(semilla)
    salida.mkdir(parents=True, exist_ok=True)
    n_clientes = max(40, int(math.ceil(filas_objetivo / CDR_POR_CLIENTE)))
    clientes = generar_clientes(n_clientes, rng)
    activos = np.flatnonzero(clientes.estado.to_numpy() == "ACTIVO")
    intensidad = rng.lognormal(0, 0.6, len(activos))
    empresarial = clientes.segmento.to_numpy()[activos] == "EMPRESARIAL"
    intensidad = np.where(empresarial, intensidad * 1.8, intensidad)
    pesos_acum = np.cumsum(intensidad)

    PLANES.to_csv(salida / "planes.csv", index=False, lineterminator="\n")
    clientes.to_csv(salida / "clientes.csv", index=False, encoding="latin-1", lineterminator="\n")

    acum = Acumulador(n_clientes)
    # pyarrow pone comillas a los nombres de columna, así que el encabezado lo escribimos nosotros
    opciones_csv = pacsv.WriteOptions(include_header=False, delimiter="|", quoting_style="none")
    opciones_ancho = pacsv.WriteOptions(include_header=False, quoting_style="none")
    archivos = []
    escritor_csv = escritor_ancho = None
    generadas = 0
    inicio = time.perf_counter()
    try:
        while generadas < filas_objetivo:
            n = min(FILAS_POR_LOTE, filas_objetivo - generadas)
            lote = generar_lote(generadas + 1, n, clientes, pesos_acum, activos, rng, acum)
            if formato in ("csv", "ambos"):
                tabla = tabla_csv(lote)
                if escritor_csv is None:
                    destino = pa.OSFile(str(salida / "cdr.csv"), "wb")
                    destino.write(("|".join(tabla.column_names) + "\n").encode("utf-8"))
                    archivos.append(destino)
                    escritor_csv = pacsv.CSVWriter(destino, tabla.schema, write_options=opciones_csv)
                escritor_csv.write_table(tabla)
            if formato in ("ancho", "ambos"):
                tabla = tabla_ancho_fijo(lote)
                if escritor_ancho is None:
                    destino = pa.OSFile(str(salida / "cdr_ancho_fijo.txt"), "wb")
                    archivos.append(destino)
                    escritor_ancho = pacsv.CSVWriter(destino, tabla.schema, write_options=opciones_ancho)
                escritor_ancho.write_table(tabla)
            generadas += n
            if filas_objetivo > FILAS_POR_LOTE:
                avance = generadas / filas_objetivo
                transcurrido = time.perf_counter() - inicio
                restante = transcurrido / avance * (1 - avance)
                print(f"\r  CDR: {generadas:,} de {filas_objetivo:,} ({avance:.0%}) · faltan ~{restante / 60:.0f} min   ", end="", flush=True)
    finally:
        for escritor in (escritor_csv, escritor_ancho):
            if escritor:
                escritor.close()
        for archivo in archivos:
            archivo.close()
    if filas_objetivo > FILAS_POR_LOTE:
        print()

    correctas = calcular_facturas(clientes, acum)
    emitidas, resumen_fact = sembrar_errores_factura(correctas, rng)
    emitidas.to_csv(salida / "facturas.csv", index=False, lineterminator="\n")

    mb_por_cliente = acum.milli_mb / 1000
    top = np.argsort(-acum.milli_mb, kind="stable")[:5]
    esperado = {
        "descripcion": "Resultados correctos de este conjunto de datos. Úsalos para comprobar tus programas.",
        "tamano": etiqueta,
        "semilla": semilla,
        "periodo": PERIODO,
        "generado": date.today().isoformat(),
        "archivos": sorted(p.name for p in salida.iterdir() if p.suffix in (".csv", ".txt")),
        "clientes": {
            "total": n_clientes,
            "activos": int(len(activos)),
            "por_segmento": clientes.segmento.value_counts().sort_index().to_dict(),
            "por_plan": clientes.plan_id.value_counts().sort_index().to_dict(),
        },
        "cdr": {
            "registros_totales": int(acum.total),
            "registros_validos": int(acum.total - sum(acum.errores.values())),
            "errores": acum.errores,
            "validos_por_tipo": acum.por_tipo,
            "minutos_nacionales": int(acum.min_nac.sum()),
            "minutos_internacionales": int(acum.min_int.sum()),
            "mb_totales": round(float(acum.milli_mb.sum()) / 1000, 3),
            "sms_totales": int(acum.sms.sum()),
            "lineas_con_consumo": int(np.sum(acum.cdr_validos > 0)),
            "validos_por_dia": {f"2026-09-{d + 1:02d}": int(v) for d, v in enumerate(acum.por_dia)},
            "llamadas_por_hora": {f"{h:02d}": int(v) for h, v in enumerate(acum.por_hora_voz)},
            "top5_lineas_mb": [
                {"linea": int(clientes.linea[i]), "cliente_id": clientes.cliente_id[i], "mb": round(float(mb_por_cliente[i]), 3)} for i in top
            ],
        },
        "facturacion": {
            "facturas": int(len(emitidas)),
            "total_facturado": int(emitidas.total.sum()),
            "total_correcto": int(correctas.total.sum()),
            **resumen_fact,
            "iva_correcto": int(correctas.iva.sum()),
        },
    }
    (salida / "esperado.json").write_text(json.dumps(esperado, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "LEEME.md").write_text(
        f"# Datos sintéticos PyDatos ({etiqueta})\n\nGenerados con semilla {semilla}. Son datos FALSOS creados para practicar.\n"
        "La descripción de cada archivo y las reglas de facturación están en la página del curso: Referencia → Datos del curso.\n",
        encoding="utf-8",
    )
    return esperado


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera datos sintéticos de facturación telco.")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--tamano", choices=TAMANOS, default="10MB", help="tamaño aproximado de cdr.csv")
    grupo.add_argument("--filas", type=int, help="número exacto de CDR (en lugar de --tamano)")
    parser.add_argument("--formato", choices=["csv", "ancho", "ambos"], default="csv", help="formato de los CDR (por defecto csv)")
    parser.add_argument("--semilla", type=int, default=2026)
    parser.add_argument("--multiplicar-errores", type=float, default=1, help="multiplica la tasa de errores sembrados (útil para muestras pequeñas)")
    parser.add_argument("--salida", type=Path, help="carpeta de salida (por defecto datos/<tamaño>)")
    args = parser.parse_args()

    global TASA_DUPLICADO
    for clave in TASA_ERROR:
        TASA_ERROR[clave] *= args.multiplicar_errores
    TASA_DUPLICADO *= args.multiplicar_errores

    if args.filas:
        filas, etiqueta = args.filas, f"{args.filas}filas"
    else:
        filas, etiqueta = int(TAMANOS[args.tamano] / BYTES_POR_FILA_CSV), args.tamano
    salida = args.salida or RAIZ / "datos" / etiqueta
    bytes_estimados = filas * BYTES_POR_FILA_CSV * (2.1 if args.formato == "ambos" else 1.1 if args.formato == "ancho" else 1)
    libre = shutil.disk_usage(salida.parent if salida.parent.exists() else RAIZ).free
    if bytes_estimados > libre * 0.9:
        print(f"❌ No hay espacio suficiente: se necesitan ~{bytes_estimados / 1e9:.1f} GB y hay {libre / 1e9:.1f} GB libres.")
        return 1

    print(f"Generando {filas:,} CDR en {salida} (formato: {args.formato}, semilla: {args.semilla})…")
    inicio = time.perf_counter()
    esperado = generar(filas, salida, args.formato, args.semilla, etiqueta)
    print(f"✅ Listo en {time.perf_counter() - inicio:.0f} s · {esperado['clientes']['total']:,} clientes · "
          f"{esperado['cdr']['registros_totales']:,} registros CDR · resultados correctos en esperado.json")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
