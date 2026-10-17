"""Pruebas del ejercicio m23-e8."""

import numpy as np
import pytest
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import evaluacion as ev

X, Y = make_classification(n_samples=3000, n_features=12, n_informative=5, weights=[0.93], class_sep=1.0, random_state=4)


def modelo():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


def test_costo():
    y = np.array([1, 1, 0, 0, 0])
    p = np.array([0.9, 0.2, 0.6, 0.1, 0.4])
    assert ev.costo(y, p, 0.5, 10, 100) == 1 * 10 + 1 * 100
    assert ev.costo(y, p, 0.15, 10, 100) == 2 * 10
    assert ev.costo(y, p, 0.95, 10, 100) == 200
    assert type(ev.costo(y, p, 0.5, 10, 100)) is int


def test_elegir_umbral():
    rng = np.random.default_rng(0)
    y = (rng.random(500) < 0.1).astype(int)
    p = np.clip(y * 0.4 + rng.random(500) * 0.6, 0, 1)
    umbral, c = ev.elegir_umbral(y, p, 5_000, 80_000)
    candidatos = np.round(np.arange(0.01, 1.0, 0.01), 2)
    costos = [ev.costo(y, p, u, 5_000, 80_000) for u in candidatos]
    assert c == min(costos)
    assert umbral == max(u for u, x in zip(candidatos, costos) if x == min(costos)), "En empate, el umbral mayor"


def test_umbrales_propios():
    y = np.array([0, 1])
    p = np.array([0.3, 0.7])
    assert ev.elegir_umbral(y, p, 1, 1, umbrales=[0.2, 0.5, 0.8]) == (0.5, 0)


def test_fuera_de_muestra():
    p = ev.probabilidades_fuera_de_muestra(modelo(), X, Y)
    esperado = cross_val_predict(modelo(), X, Y, cv=StratifiedKFold(5, shuffle=True, random_state=0),
                                 method="predict_proba")[:, 1]
    assert np.allclose(p, esperado)


def test_validacion_cruzada():
    m = ev.validacion_cruzada(modelo(), X, Y)
    assert sorted(m) == ["average_precision", "precision", "recall"]
    for media, desviacion in m.values():
        assert 0 <= media <= 1 and 0 <= desviacion < 0.3
        assert media == round(media, 3)
    assert m == ev.validacion_cruzada(modelo(), X, Y), "Reproducible con la misma semilla"


def test_informe():
    r = ev.informe(modelo(), X, Y, costo_fp=5_000, costo_fn=80_000)
    p = ev.probabilidades_fuera_de_muestra(modelo(), X, Y)
    assert (r["umbral"], r["costo_modelo"]) == ev.elegir_umbral(Y, p, 5_000, 80_000)
    assert r["costo_sin_modelo"] == int(Y.sum()) * 80_000
    assert r["costo_revisar_todo"] == int((Y == 0).sum()) * 5_000
    assert r["ahorro"] == min(r["costo_sin_modelo"], r["costo_revisar_todo"]) - r["costo_modelo"]
    assert r["ahorro"] > 0, "El modelo debe ahorrar frente a las dos estrategias sin modelo"
    assert r["umbral"] < 0.5, "Con un falso negativo 16 veces más caro, conviene un umbral bajo"
    assert "recall" in r["metricas"]
