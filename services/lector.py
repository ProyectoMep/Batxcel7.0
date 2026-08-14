"""Lectura robusta de Excel/CSV. Detecta separador y encoding en CSV,
normaliza nombres de columnas a minúsculas. Usado tanto por el análisis
de columnas del formulario de Métricas como, más adelante, por el motor
de generación de reportes."""
import pandas as pd
from pathlib import Path


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().strip('"').strip("'").strip() for c in df.columns]
    return df


def leer_excel_o_csv(ruta, dtype=str, hoja: str = None, skiprows=None,
                     solo_encabezados: bool = False) -> pd.DataFrame | None:
    """
    Lee .xlsx/.xls/.csv y retorna DataFrame con columnas normalizadas,
    o None si falla. CSV: detecta separador (, o ;) y prueba encodings
    utf-8-sig, utf-8 y latin-1.
    solo_encabezados=True: lee 0 filas de datos (rápido, solo para
    detectar los nombres de columna).
    """
    ruta = Path(ruta)
    if not ruta.exists():
        return None

    nrows = 0 if solo_encabezados else None
    ext = ruta.suffix.lower()
    try:
        if ext == ".csv":
            with open(ruta, "r", encoding="utf-8-sig", errors="ignore") as f:
                primera = f.readline()
            sep = ";" if primera.count(";") > primera.count(",") else ","
            configs = [
                (sep, "utf-8-sig"), (sep, "utf-8"),
                ("," if sep == ";" else ";", "utf-8-sig"),
                (",", "latin-1"), (";", "latin-1"),
            ]
            for s, enc in configs:
                try:
                    df = pd.read_csv(ruta, sep=s, encoding=enc, dtype=dtype,
                                     on_bad_lines="skip", skiprows=skiprows, nrows=nrows)
                    if len(df.columns) > 1:
                        return normalizar_columnas(df)
                except Exception:
                    continue
            return None

        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(ruta, sheet_name=hoja or 0, dtype=dtype,
                               skiprows=skiprows, nrows=nrows)
            return normalizar_columnas(df)

        return None
    except Exception:
        return None