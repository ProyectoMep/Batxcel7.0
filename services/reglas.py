"""Motor de reglas: evalúa objetos Condicion (de models/metrica.py) contra
un DataFrame real usando operaciones vectorizadas de pandas. Reemplaza el
parser de strings +x+/*x*/[] del sistema original — aquí las condiciones
ya vienen estructuradas, así que no hay que interpretar texto, solo
ejecutar.
"""
import pandas as pd
from models.metrica import Condicion


def resolver_columna(df: pd.DataFrame, nombre_solicitado: str) -> str | None:
    """
    Encuentra el nombre real de una columna sin importar mayúsculas,
    espacios o comillas. Si no hay coincidencia exacta, intenta una
    coincidencia parcial (la columna solicitada está contenida en el
    nombre real). Retorna None si no existe.
    """
    if not nombre_solicitado:
        return None
    objetivo = str(nombre_solicitado).strip().strip('"').strip("'").strip().lower()

    for col in df.columns:
        if str(col).strip().lower() == objetivo:
            return col

    candidatos = [col for col in df.columns if objetivo in str(col).strip().lower()]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def _es_vacio(serie: pd.Series) -> pd.Series:
    """True donde el valor es NaN, '', 'nan', 'none', 'n/a', 'na' o '[]'."""
    s = serie.astype(str).str.strip().str.lower()
    return serie.isna() | s.isin(["", "nan", "none", "n/a", "na", "[]"])


def evaluar_condicion(df: pd.DataFrame, condicion: Condicion) -> pd.Series:
    """
    Evalúa una sola Condicion contra el DataFrame. Retorna una máscara
    booleana (pd.Series) del mismo largo que df. Si la columna no existe,
    retorna todo False (para no romper el pipeline con un KeyError).
    """
    col_real = resolver_columna(df, condicion.columna)
    if col_real is None:
        return pd.Series(False, index=df.index)

    serie = df[col_real]

    if condicion.operador == "vacio":
        return _es_vacio(serie)
    if condicion.operador == "no_vacio":
        return ~_es_vacio(serie)

    s = serie.astype(str).str.strip()
    valor = str(condicion.valor).strip()

    if condicion.operador == "igual":
        return s.str.lower() == valor.lower()
    if condicion.operador == "distinto":
        return s.str.lower() != valor.lower()
    if condicion.operador == "contiene":
        return s.str.contains(valor, case=False, na=False, regex=False)
    if condicion.operador == "no_contiene":
        return ~s.str.contains(valor, case=False, na=False, regex=False)

    # Operador desconocido: no debería pasar (Condicion valida en __post_init__)
    return pd.Series(False, index=df.index)


def evaluar_grupo(df: pd.DataFrame, grupo: list[Condicion]) -> pd.Series:
    """Combina condiciones de un grupo con AND."""
    mascara = pd.Series(True, index=df.index)
    for condicion in grupo:
        mascara &= evaluar_condicion(df, condicion)
    return mascara


def evaluar_grupos(df: pd.DataFrame, grupos: list[list[Condicion]]) -> pd.Series:
    """
    Combina varios grupos con OR (cada grupo internamente es AND).
    Si la lista de grupos está vacía, retorna todo True (sin criterios
    definidos = coincide con todas las filas, igual que el sistema original
    cuando 'criterios' venía vacío en reportes.json).
    """
    if not grupos:
        return pd.Series(True, index=df.index)

    mascara = pd.Series(False, index=df.index)
    for grupo in grupos:
        mascara |= evaluar_grupo(df, grupo)
    return mascara