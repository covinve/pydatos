"""Ejercicio m20-e7: que `mypy --strict` pase sin errores (y que el código haga lo que dice).

    python -m mypy --strict ejercicios/m20-e7/facturas_tipadas.py

Reglas:
  - Anota TODAS las funciones (parámetros y retorno), con tipos precisos (nada de Any ni comentarios para silenciar a mypy).
  - mypy va a encontrar errores reales: corrígelos. En particular:
      * valor_voz debe lanzar PlanNoEncontrado si el plan no existe.
      * reporte con una lista de consumos vacía termina en "Promedio: -".
"""

import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    plan_id: str
    cargo_fijo: int
    minutos_incluidos: int
    tarifa_minuto: int


class PlanNoEncontrado(LookupError):
    pass


def leer_planes(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return {
            p["plan_id"]: Plan(p["plan_id"], p["cargo_fijo"], int(p["minutos_incluidos"]), int(p["tarifa_minuto"]))
            for p in csv.DictReader(f)
        }


def buscar(planes, plan_id):
    return planes.get(plan_id)


def valor_voz(planes, plan_id, minutos):
    plan = buscar(planes, plan_id)
    if plan.minutos_incluidos == -1:
        return 0
    return max(0, minutos - plan.minutos_incluidos) * plan.tarifa_minuto


def total_por_plan(consumos):
    totales = {}
    for plan_id, valor in consumos:
        totales[plan_id] = totales.get(plan_id, 0) + valor
    return totales


def formatear(valor):
    return "$" + f"{valor:,}".replace(",", ".")


def promedio(valores):
    if not valores:
        return None
    return sum(valores) / len(valores)


def reporte(planes, consumos):
    lineas = []
    for plan_id, total in sorted(total_por_plan(consumos).items()):
        lineas.append(f"{plan_id}: {formatear(total)} (cargo {formatear(planes[plan_id].cargo_fijo)})")
    prom = promedio([v for _, v in consumos])
    lineas.append("Promedio: " + formatear(round(prom)))
    return "\n".join(lineas)
