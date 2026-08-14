"""Compara lo que hace nuestro leer_excel_o_csv real contra un pandas
crudo, para encontrar dónde se pierden columnas.

Uso: python scripts/diagnostico_lector.py input/PCR.csv
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.lector import leer_excel_o_csv


def main():
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "input/PCR.csv")

    print("── Usando NUESTRA función leer_excel_o_csv, sin skiprows ──")
    df1 = leer_excel_o_csv(ruta)
    print(f"  Columnas ({len(df1.columns) if df1 is not None else 0}): "
          f"{list(df1.columns) if df1 is not None else 'FALLÓ'}")

    print("\n── Usando NUESTRA función leer_excel_o_csv, con skiprows=[1] ──")
    df2 = leer_excel_o_csv(ruta, skiprows=[1])
    print(f"  Columnas ({len(df2.columns) if df2 is not None else 0}): "
          f"{list(df2.columns) if df2 is not None else 'FALLÓ'}")


if __name__ == "__main__":
    main()