import os
import json
from typing import Optional

def minutos(segundos):
    return (segundos+59)//60

def agregar_rechazo(cdr_id, motivo, rechazos=[]):
    rechazos.append((cdr_id, motivo))
    return rechazos

def leer_umbral(texto):
    try:
        return float(texto)
    except:
        return 5.0

def plan_o_defecto(planes: dict, plan_id: str) -> Optional[str]:
    return planes.get(plan_id, None)
