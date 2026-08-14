"""Registro de funciones especiales: lógica que no cabe en el formato
columna/operador/valor (ej. comparar versiones de sistema operativo
contra un maestro). Cada Metrica puede referenciar una de estas
funciones por nombre en su campo 'funcion_especial'; el generador de
reporte la ejecuta sobre el DataFrame después de los cruces normales y
antes de evaluar incumplimiento/cumplimiento.
"""
import re
import pandas as pd
from services.reglas import resolver_columna
from services.resolver_archivo import resolver_archivo_por_patron
from services.lector import leer_excel_o_csv
from config.settings import TEMPLATES_MAESTROS_DIR

VERSION_ANDROID_DEPRECADA = 13
VERSION_IOS_DEPRECADA = 17


def _a_tupla_version(valor):
    if valor is None:
        return None
    s = str(valor).strip()
    if not s or s.lower() in ("nan", "none", "n/a", "na"):
        return None
    m = re.search(r"\d+(?:\.\d+)*", s)
    if not m:
        return None
    return tuple(int(p) for p in m.group(0).split("."))


def _comparar_versiones(a, b) -> int | None:
    ta, tb = _a_tupla_version(a), _a_tupla_version(b)
    if ta is None or tb is None:
        return None
    largo = max(len(ta), len(tb))
    ta += (0,) * (largo - len(ta))
    tb += (0,) * (largo - len(tb))
    if ta < tb:
        return -1
    if ta > tb:
        return 1
    return 0


def calcular_moviles_os_al_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cruza con el maestro MOVILES OS (columnas: dispositivo, ultima
    actualizacion) por 'model', y agrega:
      - 'ultima actualizacion' (traída del maestro)
      - 'os al dia' ('actualizado' / 'desactualizado (X)' / 'N/A')
      - 'deprecado' ('DEPRECADO' / 'OK')
    Si falta el maestro o las columnas necesarias, rellena con 'N/A' y
    sigue sin romper el pipeline.
    """
    df = df.copy()
    col_model = resolver_columna(df, "model")
    col_ver = resolver_columna(df, "os version")
    col_os = resolver_columna(df, "os")

    ruta_maestro = resolver_archivo_por_patron(
        "MOVILES OS(NO QUITAR, CAMBIAR).xlsx", TEMPLATES_MAESTROS_DIR)

    if ruta_maestro is None or col_model is None or col_ver is None:
        print("  ⚠️  moviles_os_al_dia: falta el maestro o columnas model/os version")
        df["ultima actualizacion"] = "N/A"
        df["os al dia"] = "N/A"
        df["deprecado"] = "N/A"
        return df

    maestro = leer_excel_o_csv(ruta_maestro)
    if maestro is None:
        df["ultima actualizacion"] = "N/A"
        df["os al dia"] = "N/A"
        df["deprecado"] = "N/A"
        return df

    col_disp = resolver_columna(maestro, "dispositivo")
    col_ult = resolver_columna(maestro, "ultima actualizacion")
    if col_disp is None or col_ult is None:
        df["ultima actualizacion"] = "N/A"
        df["os al dia"] = "N/A"
        df["deprecado"] = "N/A"
        return df

    mapa = {}
    for _, fila in maestro.iterrows():
        clave = str(fila[col_disp]).strip().lower()
        if clave and clave != "nan":
            mapa[clave] = fila[col_ult]

    df["ultima actualizacion"] = df[col_model].apply(
        lambda modelo: mapa.get(str(modelo).strip().lower()))

    def evaluar_al_dia(row):
        ultima = row["ultima actualizacion"]
        actual = row.get(col_ver)
        if ultima is None or pd.isna(ultima):
            return "N/A"
        cmp = _comparar_versiones(actual, ultima)
        if cmp is None:
            return "N/A"
        return "actualizado" if cmp >= 0 else f"desactualizado ({ultima})"

    df["os al dia"] = df.apply(evaluar_al_dia, axis=1)

    def evaluar_deprecado(row):
        if col_os is None:
            return "OK"
        os_val = str(row.get(col_os, "")).lower()
        actual = row.get(col_ver)
        if "android" in os_val:
            cmp = _comparar_versiones(actual, VERSION_ANDROID_DEPRECADA)
            return "DEPRECADO" if (cmp is not None and cmp < 0) else "OK"
        if "ios" in os_val:
            cmp = _comparar_versiones(actual, VERSION_IOS_DEPRECADA)
            return "DEPRECADO" if (cmp is not None and cmp < 0) else "OK"
        return "OK"

    df["deprecado"] = df.apply(evaluar_deprecado, axis=1)

    print(f"  ✅ moviles_os_al_dia: calculado sobre {len(df)} fila(s)")
    return df


REGISTRO = {
    "moviles_os_al_dia": calcular_moviles_os_al_dia,
}


def aplicar_funcion_especial(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    funcion = REGISTRO.get(nombre)
    if funcion is None:
        print(f"  ⚠️  Función especial no registrada: {nombre}")
        return df
    return funcion(df)