"""Orquestador principal: recorre todas las métricas incluidas en el
reporte, aplica cruces + incumplimiento + limpieza, separa por entidad,
arma el Excel final (hojas + resúmenes) y calcula el cumplimiento de
cada una. Al finalizar, mueve los archivos de input/ a procesados/<fecha>/.
Reemplaza src/pipeline.py + src/procesos/*.py del sistema original.
"""
from datetime import date
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook

from config.settings import OUTPUT_DIR
from models.metrica import MetricaRepository
from models.entidad import EntidadRepository
from services.resolver_archivo import resolver_archivo_de_metrica
from services.lector import leer_excel_o_csv
from services.cruces import aplicar_enriquecimientos
from services.reglas import evaluar_grupos, resolver_columna
from services.separador_entidad import separar_por_entidad
from services.cumplimiento import calcular_cumplimiento
from services.formato_excel import (aplicar_formato_encabezados,
                                    colorear_pestanas_resumen,
                                    reordenar_hojas_por_categoria)
from services.historico import mover_inputs_a_procesados
from services.softerra import generar_softerra
from services.reglas_especiales import aplicar_funcion_especial


def _limpiar_id_columna(df: pd.DataFrame, col_id: str, texto_a_quitar: str) -> pd.DataFrame:
    df = df.copy()
    df[col_id] = df[col_id].apply(
        lambda x: str(x).replace(texto_a_quitar, "").strip() if pd.notna(x) else x)
    return df


def _construir_resumen(hojas_por_categoria: dict) -> dict[str, pd.DataFrame]:
    """hojas_por_categoria: {categoria: {nombre_hoja: (df, col_id)}}
    Retorna {categoria: DataFrame matriz ID x hoja con 'X'}."""
    resumenes = {}
    for categoria, hojas in hojas_por_categoria.items():
        matriz = {}
        for nombre_hoja, (df, col_id) in hojas.items():
            if col_id is None or col_id not in df.columns or df.empty:
                continue
            for id_val in df[col_id].dropna().unique():
                id_str = str(id_val).strip()
                if not id_str:
                    continue
                matriz.setdefault(id_str, {})[nombre_hoja] = "X"

        if matriz:
            df_res = pd.DataFrame.from_dict(matriz, orient="index").fillna("")
            df_res.index.name = "ID"
            df_res.reset_index(inplace=True)
            otras = sorted([c for c in df_res.columns if c != "ID"])
            df_res = df_res[["ID"] + otras]
        else:
            df_res = pd.DataFrame(columns=["ID"])
        resumenes[categoria] = df_res
    return resumenes


def generar_reporte(fecha: str = None, mover_procesados: bool = True) -> dict:
    """
    Ejecuta el pipeline completo. Retorna:
    {'ok': True, 'fecha': str, 'archivos': [...], 'movidos_a_procesados': int}  o
    {'ok': False, 'fecha': str, 'error': str}

    mover_procesados: si True (por defecto), al terminar exitosamente
    mueve todo el contenido de input/ a procesados/<fecha>/, para que la
    próxima semana no se reprocesen los mismos archivos por error.
    """
    fecha = fecha or date.today().isoformat()
    metrica_repo = MetricaRepository()
    entidad_repo = EntidadRepository()

    metricas = metrica_repo.listar()
    entidades = entidad_repo.listar()

    if not entidades:
        return {"ok": False, "fecha": fecha,
                "error": "No hay entidades configuradas (ve a la sección Entidades)"}

    hojas_por_entidad = {e.nombre: {} for e in entidades}
    categoria_por_entidad = {e.nombre: {} for e in entidades}
    cumplimiento_por_entidad = {e.nombre: [] for e in entidades}

    print("\n🔗 Generando softerra...")
    generar_softerra()

    for metrica in metricas:
        print(f"\n📄 Procesando métrica: {metrica.nombre}")
        ruta, es_respaldo = resolver_archivo_de_metrica(metrica)

        if ruta is None:
            if metrica.obligatoria:
                return {"ok": False, "fecha": fecha,
                        "error": f"Falta el archivo de la métrica obligatoria '{metrica.nombre}' "
                                 f"(patrón: {metrica.archivo_patron})"}
            print(f"   ⚠️  Métrica opcional omitida (archivo no encontrado)")
            continue

        df = leer_excel_o_csv(ruta)
        if df is None:
            if metrica.obligatoria:
                return {"ok": False, "fecha": fecha,
                        "error": f"No se pudo leer el archivo de '{metrica.nombre}': {ruta.name}"}
            print(f"   ⚠️  Métrica opcional omitida (no se pudo leer el archivo)")
            continue

        if metrica.enriquecimientos:
            df = aplicar_enriquecimientos(df, metrica.enriquecimientos)

        if metrica.funcion_especial:
            df = aplicar_funcion_especial(df, metrica.funcion_especial)

        if metrica.cumplimiento.aplica:
            universo_por_entidad = separar_por_entidad(df, metrica.columnas_separacion, entidades)
            for entidad in entidades:
                df_universo_ent = universo_por_entidad.get(entidad.nombre, df)
                filtro_extra = metrica.filtro_entidad.get(entidad.nombre)
                if filtro_extra:
                    mascara_extra = evaluar_grupos(df_universo_ent, filtro_extra)
                    df_universo_ent = df_universo_ent[mascara_extra]
                resultado = calcular_cumplimiento(df_universo_ent, metrica)
                cumplimiento_por_entidad[entidad.nombre].append(resultado)

        if not metrica.incluir_en_reporte:
            continue

        mascara_incumplimiento = evaluar_grupos(df, metrica.criterios_incumplimiento)
        df_hoja = df[mascara_incumplimiento].copy()
        print(f"   Filtrado: {len(df_hoja)} de {len(df)} fila(s)")

        col_id_real = resolver_columna(df_hoja, metrica.columna_id)
        if col_id_real and metrica.limpiar_id:
            df_hoja = _limpiar_id_columna(df_hoja, col_id_real, metrica.limpiar_id)

        hojas_separadas = separar_por_entidad(df_hoja, metrica.columnas_separacion, entidades)

        for entidad in entidades:
            df_ent = hojas_separadas.get(entidad.nombre, df_hoja).copy()

            filtro_extra = metrica.filtro_entidad.get(entidad.nombre)
            if filtro_extra:
                mascara_extra = evaluar_grupos(df_ent, filtro_extra)
                antes_extra = len(df_ent)
                df_ent = df_ent[mascara_extra]
                if antes_extra != len(df_ent):
                    print(f"   🎯 {entidad.nombre}/{metrica.nombre}: "
                          f"{antes_extra} → {len(df_ent)} tras filtro específico de entidad")

            if metrica.criterios_limpieza:
                mascara_eliminar = evaluar_grupos(df_ent, metrica.criterios_limpieza)
                antes = len(df_ent)
                df_ent = df_ent[~mascara_eliminar]
                if antes != len(df_ent):
                    print(f"   🧹 {entidad.nombre}/{metrica.nombre}: "
                          f"{antes} → {len(df_ent)} tras limpieza")

            col_id_ent = resolver_columna(df_ent, metrica.columna_id)
            hojas_por_entidad[entidad.nombre][metrica.nombre] = (df_ent, col_id_ent)

            if metrica.categoria:
                categoria_por_entidad[entidad.nombre].setdefault(
                    metrica.categoria, {})[metrica.nombre] = (df_ent, col_id_ent)

    carpeta_salida = OUTPUT_DIR / fecha
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    archivos_generados = []

    for entidad in entidades:
        nombre_archivo = f"{entidad.nombre_archivo_salida or entidad.nombre}.xlsx"
        ruta_salida = carpeta_salida / nombre_archivo

        resumenes = _construir_resumen(categoria_por_entidad[entidad.nombre])

        with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
            for nombre_hoja, (df_hoja, _col_id) in hojas_por_entidad[entidad.nombre].items():
                df_hoja.to_excel(writer, sheet_name=nombre_hoja[:31], index=False)
            for categoria, df_res in resumenes.items():
                nombre_resumen = f"Resumen_{categoria.replace(' ', '_')}"[:31]
                df_res.to_excel(writer, sheet_name=nombre_resumen, index=False)

        wb = load_workbook(ruta_salida)
        aplicar_formato_encabezados(wb)
        colorear_pestanas_resumen(wb)
        mapa_categoria = {m.nombre[:31]: m.categoria for m in metricas if m.categoria}
        reordenar_hojas_por_categoria(wb, mapa_categoria)
        wb.save(ruta_salida)
        wb.close()

        archivos_generados.append(nombre_archivo)
        print(f"\n💾 Guardado: {ruta_salida}")

        if cumplimiento_por_entidad[entidad.nombre]:
            filas = [r for r in cumplimiento_por_entidad[entidad.nombre] if r.get("aplica")]
            df_cump = pd.DataFrame(filas, columns=[
                "metrica", "denominador", "numerador", "resultado", "umbral", "operador", "estado"])
            ruta_cump = carpeta_salida / f"resumen_cumplimiento_{entidad.nombre.lower()}.xlsx"
            df_cump.to_excel(ruta_cump, index=False)
            archivos_generados.append(ruta_cump.name)
            print(f"💾 Guardado: {ruta_cump}")

    movidos = 0
    if mover_procesados:
        movidos = mover_inputs_a_procesados(fecha)
        print(f"\n📦 {movidos} archivo(s) movidos a procesados/{fecha}/")

    return {"ok": True, "fecha": fecha, "archivos": archivos_generados,
            "movidos_a_procesados": movidos}