"""Motor de cruces (enriquecimiento): trae columnas de un archivo externo
hacia el DataFrame base, usando una columna en común. Usa merge vectorizado
de pandas (rápido) en vez del loop fila por fila del sistema original.
Busca el archivo externo primero en input/, y si no está ahí (ej. un
maestro como USER.xlsx que no cambia semana a semana), en
templates_maestros/maestros/.
"""
import pandas as pd
from models.metrica import Enriquecimiento
from services.reglas import resolver_columna
from services.resolver_archivo import resolver_archivo_por_patron
from services.lector import leer_excel_o_csv
from config.settings import INPUT_DIR, TEMPLATES_MAESTROS_DIR


def _resolver_archivo_cruce(patron: str):
    ruta = resolver_archivo_por_patron(patron, INPUT_DIR)
    if ruta is not None:
        return ruta
    return resolver_archivo_por_patron(patron, TEMPLATES_MAESTROS_DIR)


def aplicar_enriquecimiento(df_base: pd.DataFrame, enriquecimiento: Enriquecimiento) -> pd.DataFrame:
    """
    Cruza df_base con el archivo externo definido en 'enriquecimiento' y
    agrega las columnas solicitadas. Si el archivo externo no se encuentra
    o las columnas no existen, retorna df_base sin cambios (no rompe el
    pipeline) e imprime una advertencia.
    """
    ruta = _resolver_archivo_cruce(enriquecimiento.archivo_patron)
    if ruta is None:
        print(f"  ⚠️  Cruce omitido: no se encontró '{enriquecimiento.archivo_patron}' "
              f"en input/ ni en templates_maestros/")
        return df_base

    df_externo = leer_excel_o_csv(ruta)
    if df_externo is None:
        print(f"  ⚠️  Cruce omitido: no se pudo leer {ruta.name}")
        return df_base

    col_base = resolver_columna(df_base, enriquecimiento.columna_base)
    col_cruzar = resolver_columna(df_externo, enriquecimiento.columna_cruzar)
    if col_base is None or col_cruzar is None:
        print(f"  ⚠️  Cruce omitido: columna no encontrada "
              f"(base='{enriquecimiento.columna_base}'→{col_base}, "
              f"cruzar='{enriquecimiento.columna_cruzar}'→{col_cruzar})")
        return df_base

    columnas_reales_extraer = []
    for nombre in enriquecimiento.columnas_extraer:
        col_real = resolver_columna(df_externo, nombre)
        if col_real is None:
            print(f"  ⚠️  Columna a extraer no encontrada en archivo externo: '{nombre}'")
            continue
        columnas_reales_extraer.append(col_real)

    if not columnas_reales_extraer:
        return df_base

    df_base = df_base.copy()
    clave_base = df_base[col_base].astype(str).str.strip()
    if enriquecimiento.texto_a_quitar_del_base:
        clave_base = clave_base.str.replace(
            enriquecimiento.texto_a_quitar_del_base, "", regex=False)
    df_base["_clave_cruce"] = clave_base.str.strip().str.lower()

    derecha = df_externo.copy()
    columnas_para_derecha = []
    for c in [col_cruzar] + columnas_reales_extraer:
        if c not in columnas_para_derecha:
            columnas_para_derecha.append(c)
    derecha = derecha[columnas_para_derecha].copy()
    derecha["_clave_cruce"] = derecha[col_cruzar].astype(str).str.strip().str.lower()
    derecha = derecha.drop_duplicates("_clave_cruce")[["_clave_cruce"] + columnas_reales_extraer]

    columnas_a_pisar = [c for c in columnas_reales_extraer if c in df_base.columns]
    if columnas_a_pisar:
        df_base = df_base.drop(columns=columnas_a_pisar)

    df_base = df_base.merge(derecha, on="_clave_cruce", how="left")
    df_base = df_base.drop(columns=["_clave_cruce"])

    coincidencias = df_base[columnas_reales_extraer[0]].notna().sum()
    print(f"  ✅ Cruce con {ruta.name}: {coincidencias}/{len(df_base)} coincidencias "
          f"→ {', '.join(columnas_reales_extraer)}")

    return df_base


def aplicar_enriquecimientos(df_base: pd.DataFrame, enriquecimientos: list[Enriquecimiento]) -> pd.DataFrame:
    """Aplica varios cruces en secuencia sobre el mismo DataFrame."""
    for enriquecimiento in enriquecimientos:
        df_base = aplicar_enriquecimiento(df_base, enriquecimiento)
    return df_base