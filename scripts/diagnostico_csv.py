"""Diagnóstico: muestra las columnas reales de un CSV, probando distintas
formas de skiprows, para entender su estructura real antes de configurar
softerra correctamente.

Uso: python scripts/diagnostico_csv.py input/PCR.csv
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd


def main():
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "input/PCR.csv")
    if not ruta.exists():
        print(f"❌ No existe: {ruta}")
        return

    print(f"📄 Archivo: {ruta}\n")

    print("── Primeras 5 líneas crudas del archivo ──")
    with open(ruta, "r", encoding="utf-8-sig", errors="ignore") as f:
        for i, linea in enumerate(f):
            if i >= 5:
                break
            print(f"  [{i}] {linea.rstrip()[:150]}")

    for etiqueta, skiprows in [("sin skiprows", None), ("skiprows=[1]", [1]), ("skiprows=1", 1)]:
        print(f"\n── Leyendo con {etiqueta} ──")
        try:
            df = pd.read_csv(ruta, skiprows=skiprows, nrows=3, encoding="utf-8-sig", sep=None, engine="python")
            print(f"  Columnas: {list(df.columns)}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    main()