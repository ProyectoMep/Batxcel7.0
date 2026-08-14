"""Separa un DataFrame por entidad (BSNC/SF) usando la(s) columna(s) de
separación de la métrica y los identificadores de texto de cada entidad.
Reemplaza la lógica de separacion.py del sistema original.
"""
import pandas as pd
from models.entidad import Entidad
from services.reglas import resolver_columna


def _fila_coincide(valor, identificadores: list[str]) -> bool:
    idents = [str(i).lower().strip() for i in identificadores]

    # "N/A" en los identificadores también matchea celdas vacías
    if "n/a" in idents:
        if pd.isna(valor) or str(valor).strip().upper() in ("N/A", "NA", ""):
            return True

    if pd.isna(valor):
        return False

    v = str(valor).lower().strip()
    if not v:
        return False
    return any(ident in v for ident in idents)


def serie_de_separacion(df: pd.DataFrame, columnas_separacion: list[str]) -> pd.Series | None:
    """
    Retorna la serie a usar para separar. Si hay varias columnas, por
    cada fila se usa la primera que tenga valor no vacío. None si
    ninguna de las columnas existe en el DataFrame.
    """
    columnas_reales = []
    for nombre in columnas_separacion:
        col_real = resolver_columna(df, nombre)
        if col_real:
            columnas_reales.append(col_real)
    if not columnas_reales:
        return None

    serie = df[columnas_reales[0]].copy()
    vacios = ("", "nan", "none", "n/a", "na")
    for col in columnas_reales[1:]:
        esta_vacia = serie.isna() | serie.astype(str).str.strip().str.lower().isin(vacios)
        serie = serie.where(~esta_vacia, df[col])
    return serie


def separar_por_entidad(df: pd.DataFrame, columnas_separacion: list[str],
                        entidades: list[Entidad]) -> dict[str, pd.DataFrame]:
    """
    Retorna {nombre_entidad: DataFrame filtrado} para cada entidad.
    Si no hay columna de separación detectable, cada entidad recibe el
    DataFrame completo sin filtrar (mismo comportamiento del sistema
    original cuando no existe columna 'company').
    """
    serie = serie_de_separacion(df, columnas_separacion)
    resultado = {}
    for entidad in entidades:
        if serie is None:
            resultado[entidad.nombre] = df
            continue
        mascara = serie.apply(lambda v: _fila_coincide(v, entidad.identificadores))
        resultado[entidad.nombre] = df[mascara]
    return resultado