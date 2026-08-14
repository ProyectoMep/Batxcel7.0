"""Genera input/softerra.xlsx concatenando los CSV de directorio
configurados (PCR, SBI, SEC, SNC, UNC, CO2 por defecto). Usa
resolver_columna (insensible a mayúsculas) para encontrar cada columna
deseada, y normaliza los nombres de salida a minúsculas para que todos
los archivos fuente queden alineados al concatenar, sin importar cómo
esté escrito el nombre real en cada uno.
"""
import pandas as pd
from config.settings import INPUT_DIR
from services.config_softerra import cargar_config_softerra
from services.resolver_archivo import resolver_archivo_por_patron
from services.lector import leer_excel_o_csv
from services.reglas import resolver_columna


def generar_softerra() -> dict:
    """
    Retorna {'ok': bool, 'archivo': str|None, 'filas': int,
    'fuentes_usadas': [...], 'fuentes_faltantes': [...]}
    """
    cfg = cargar_config_softerra()
    columnas_deseadas = cfg["columnas"]
    skiprows = cfg.get("skiprows")

    frames = []
    usadas, faltantes = [], []

    for fuente in cfg["fuentes"]:
        patron = fuente["patron"]
        ruta = resolver_archivo_por_patron(patron, INPUT_DIR)
        if ruta is None:
            faltantes.append(patron)
            continue

        df = leer_excel_o_csv(ruta, skiprows=skiprows)
        if df is None:
            print(f"  ❌ softerra: no se pudo leer {ruta.name}")
            faltantes.append(patron)
            continue

        # Resuelve cada columna deseada contra los nombres reales del
        # archivo (insensible a mayúsculas), y arma un mapeo
        # nombre_canonico(minúscula) -> nombre_real_en_este_archivo.
        mapeo_columnas = {}
        columnas_faltantes = []
        for col_deseada in columnas_deseadas:
            col_real = resolver_columna(df, col_deseada)
            if col_real:
                mapeo_columnas[col_deseada.lower()] = col_real
            else:
                columnas_faltantes.append(col_deseada)

        if columnas_faltantes:
            print(f"  ⚠️  softerra: {ruta.name} no tiene columnas {columnas_faltantes}, se omiten")

        if not mapeo_columnas:
            print(f"  ❌ softerra: {ruta.name} no tiene ninguna columna esperada, se omite")
            faltantes.append(patron)
            continue

        df_sel = df[list(mapeo_columnas.values())].copy()
        df_sel.columns = list(mapeo_columnas.keys())  # nombres normalizados en minúsculas
        frames.append(df_sel)
        usadas.append(ruta.name)

    if not frames:
        print("  ⚠️  softerra: no se encontró ninguna fuente, no se genera softerra.xlsx")
        return {"ok": False, "archivo": None, "filas": 0,
                "fuentes_usadas": [], "fuentes_faltantes": faltantes}

    df_final = pd.concat(frames, ignore_index=True)
    renombrar = {k.lower(): v for k, v in cfg.get("renombrar", {}).items()}
    df_final = df_final.rename(columns=renombrar)

    salida = INPUT_DIR / cfg["salida"]
    df_final.to_excel(salida, index=False)

    print(f"  ✅ softerra generado: {salida.name} ({len(df_final)} filas, "
          f"{len(usadas)}/{len(cfg['fuentes'])} fuentes)")
    print(f"     Columnas finales: {list(df_final.columns)}")
    if faltantes:
        print(f"     ⚠️  Fuentes faltantes: {', '.join(faltantes)}")

    return {"ok": True, "archivo": salida.name, "filas": len(df_final),
            "fuentes_usadas": usadas, "fuentes_faltantes": faltantes}