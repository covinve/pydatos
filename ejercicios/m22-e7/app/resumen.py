"""La aplicación que vas a empaquetar (ya está hecha): resume un cdr.csv.

    python -m app.resumen                  lee $TELCO_DATOS/cdr.csv (por defecto /datos)
                                           y escribe $TELCO_SALIDAS/resumen.json (por defecto /salidas)
"""

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path


def resumir(ruta_cdr: Path) -> dict:
    por_tipo: Counter = Counter()
    segundos = 0
    with open(ruta_cdr, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f, delimiter="|"):
            por_tipo[fila["tipo"]] += 1
            if fila["tipo"] == "VOZ" and int(fila["duracion_seg"]) >= 0:
                segundos += int(fila["duracion_seg"])
    return {"registros": sum(por_tipo.values()), "por_tipo": dict(sorted(por_tipo.items())), "segundos_voz": segundos}


def main() -> int:
    datos = Path(os.environ.get("TELCO_DATOS", "/datos"))
    salidas = Path(os.environ.get("TELCO_SALIDAS", "/salidas"))
    if not (datos / "cdr.csv").exists():
        print(f"No encuentro {datos / 'cdr.csv'}: ¿montaste el volumen de datos?", file=sys.stderr)
        return 2
    resumen = resumir(datos / "cdr.csv")
    salidas.mkdir(parents=True, exist_ok=True)
    (salidas / "resumen.json").write_text(json.dumps(resumen, indent=2), encoding="utf-8")
    print(f"{resumen['registros']} registros resumidos en {salidas / 'resumen.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
