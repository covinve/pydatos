"""Ejercicio m23-e8: evaluar un clasificador con validación cruzada y elegir el umbral por costo.

Funciones:

    costo(y, proba, umbral, costo_fp, costo_fn) -> int
        Se marca para revisión todo caso con proba >= umbral.
        costo = falsos positivos × costo_fp + falsos negativos × costo_fn.

    elegir_umbral(y, proba, costo_fp, costo_fn, umbrales=None) -> tuple[float, int]
        El umbral de menor costo y ese costo. Por defecto prueba 0.01, 0.02, ..., 0.99.
        En empate, el umbral MAYOR (se revisan menos casos).

    probabilidades_fuera_de_muestra(modelo, X, y, k=5, semilla=0) -> np.ndarray
        Probabilidad de la clase 1 de cada caso, predicha por un modelo que NO lo vio al entrenar:
        cross_val_predict(modelo, X, y, cv=StratifiedKFold(k, shuffle=True, random_state=semilla),
                          method="predict_proba")[:, 1].

    validacion_cruzada(modelo, X, y, k=5, semilla=0) -> dict
        Con cross_validate y el mismo StratifiedKFold: {"precision": (media, desviación),
        "recall": (...), "average_precision": (...)}, cada número redondeado a 3 decimales.

    informe(modelo, X, y, costo_fp, costo_fn, k=5, semilla=0) -> dict
        {"umbral": ..., "costo_modelo": ...}   elegir_umbral sobre las probabilidades fuera de muestra
        "costo_sin_modelo": no revisar nada (todos los positivos se escapan)
        "costo_revisar_todo": revisar todo (todos los negativos son falsos positivos)
        "ahorro": el menor de los dos costos anteriores menos costo_modelo
        "metricas": validacion_cruzada(...)
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
