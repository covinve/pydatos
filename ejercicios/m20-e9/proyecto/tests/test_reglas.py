from telco_calidad.reglas import agregar_rechazo, leer_umbral, minutos, plan_o_defecto


def test_minutos() -> None:
    assert [minutos(s) for s in (0, 1, 60, 61)] == [0, 1, 1, 2]


def test_agregar_rechazo_no_comparte_la_lista() -> None:
    assert agregar_rechazo("1", "duplicado") == [("1", "duplicado")]
    assert agregar_rechazo("2", "linea_vacia") == [("2", "linea_vacia")]
    propia: list[tuple[str, str]] = [("0", "x")]
    assert agregar_rechazo("3", "y", propia) == [("0", "x"), ("3", "y")]


def test_leer_umbral() -> None:
    assert leer_umbral("2.5") == 2.5
    assert leer_umbral("cinco") == 5.0
    assert leer_umbral(None) == 5.0


def test_plan_o_defecto() -> None:
    assert plan_o_defecto({"HOG30": "Hogar 30"}, "HOG30") == "Hogar 30"
    assert plan_o_defecto({}, "X") is None
