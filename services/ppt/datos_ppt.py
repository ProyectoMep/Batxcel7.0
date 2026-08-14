"""Arma los datos que necesita diseno_ppt.py para dibujar cada tarjeta.

La línea de comparación semanal ('↑ 9 con respecto a la semana pasada
(9)') se calcula como (denominador - numerador) de esta semana vs la
semana pasada — el conteo de 'no conformes' — leyendo
resumen_cumplimiento_<entidad>.xlsx actual y el de la semana anterior.
Esto reemplaza el conteo de filas de hoja que usábamos antes, que solo
funcionaba para métricas con hoja propia en el reporte.

Los 'operaciones_ppt' (ej. IOS/Android dentro de Update) se calculan
aparte, leyendo directamente las filas de la hoja fuente indicada.
"""
from pathlib import Path
import pandas as pd

from config.settings import OUTPUT_DIR
from models.metrica import MetricaRepository, Metrica
from services.reglas import evaluar_grupos
from services.ppt.diseno_ppt import formatear_comparacion


# ══════════════════════ LECTURA DE ARCHIVOS ══════════════════════

def cargar_cumplimiento(ruta: Path) -> dict[str, dict]:
    """{'nombre_metrica_en_minuscula': {umbral, numerador, denominador, resultado, estado}}."""
    if ruta is None or not Path(ruta).exists():
        return {}
    try:
        df = pd.read_excel(ruta)
    except Exception:
        return {}
    resultado = {}
    for _, fila in df.iterrows():
        nombre = str(fila.get("metrica", "")).strip()
        if not nombre:
            continue
        resultado[nombre.lower()] = {
            "umbral": fila.get("umbral", 0) or 0,
            "numerador": int(fila.get("numerador", 0) or 0),
            "denominador": int(fila.get("denominador", 0) or 0),
            "resultado": fila.get("resultado"),
            "estado": fila.get("estado", "Sin datos"),
        }
    return resultado


def buscar_archivo_anterior(nombre_archivo_sin_ext: str, fecha_actual: str) -> Path | None:
    """Busca en output/ la carpeta de fecha más reciente ANTERIOR a
    fecha_actual que contenga <nombre_archivo_sin_ext>.xlsx."""
    if not OUTPUT_DIR.exists():
        return None
    candidatos = []
    for carpeta in OUTPUT_DIR.iterdir():
        if not carpeta.is_dir() or carpeta.name >= fecha_actual:
            continue
        ruta = carpeta / f"{nombre_archivo_sin_ext}.xlsx"
        if ruta.exists():
            candidatos.append((carpeta.name, ruta))
    if not candidatos:
        return None
    candidatos.sort(key=lambda t: t[0], reverse=True)
    return candidatos[0][1]


def leer_hoja(ruta: Path, nombre_hoja: str) -> pd.DataFrame | None:
    """Lee una hoja específica de un Excel de reporte, insensible a
    mayúsculas en el nombre. None si no existe o falla."""
    if ruta is None or not Path(ruta).exists():
        return None
    try:
        xl = pd.ExcelFile(ruta)
    except Exception:
        return None
    objetivo = nombre_hoja.strip().lower()
    for hoja in xl.sheet_names:
        if hoja.strip().lower() == objetivo:
            try:
                return xl.parse(hoja)
            except Exception:
                return None
    return None


# ══════════════════════ ARMADO DE DATOS POR MÉTRICA ══════════════════════

def construir_dato_metrica(metrica: Metrica, cumplimiento_actual: dict, cumplimiento_anterior: dict) -> dict:
    """Retorna el dict que espera diseno_ppt.dibujar_tarjeta(). La
    comparación semanal usa (denominador - numerador) = cantidad de
    'no conformes', actual vs anterior."""
    clave = metrica.nombre.strip().lower()
    cump = cumplimiento_actual.get(clave)

    if cump is None:
        texto_comparacion, color_comparacion = formatear_comparacion(0, 0)
        return {
            "comparacion_texto": texto_comparacion,
            "comparacion_color": color_comparacion,
            "umbral": metrica.cumplimiento.umbral,
            "numerador": 0, "denominador": 0,
            "resultado_pct": "N/A", "estado": "Sin datos",
        }

    no_conformes_actual = cump.get("denominador", 0) - cump.get("numerador", 0)
    cump_anterior = cumplimiento_anterior.get(clave)
    no_conformes_anterior = (cump_anterior.get("denominador", 0) - cump_anterior.get("numerador", 0)
                             if cump_anterior else 0)
    texto_comparacion, color_comparacion = formatear_comparacion(no_conformes_actual, no_conformes_anterior)

    resultado = cump.get("resultado")
    resultado_pct = f"{resultado * 100:.1f}%" if isinstance(resultado, (int, float)) else "N/A"

    return {
        "comparacion_texto": texto_comparacion,
        "comparacion_color": color_comparacion,
        "umbral": cump.get("umbral") or metrica.cumplimiento.umbral,
        "numerador": cump.get("numerador", 0),
        "denominador": cump.get("denominador", 0),
        "resultado_pct": resultado_pct,
        "estado": cump.get("estado", "Sin datos"),
    }


def construir_operaciones_metrica(metrica: Metrica, ruta_reporte_actual: Path,
                                  ruta_reporte_anterior: Path | None) -> list[dict]:
    """Calcula cada operacion_ppt de la métrica (ej. IOS/Android),
    contando filas que cumplen su condición en la hoja fuente indicada,
    semana actual vs anterior. Retorna
    [{'nombre': str, 'comparacion_texto': str, 'comparacion_color': RGBColor}]."""
    resultado = []
    for op in metrica.operaciones_ppt:
        df_actual = leer_hoja(ruta_reporte_actual, op.hoja_fuente)
        n_actual = int(evaluar_grupos(df_actual, op.condicion).sum()) if df_actual is not None else 0

        df_anterior = leer_hoja(ruta_reporte_anterior, op.hoja_fuente) if ruta_reporte_anterior else None
        n_anterior = int(evaluar_grupos(df_anterior, op.condicion).sum()) if df_anterior is not None else 0

        texto, color = formatear_comparacion(n_actual, n_anterior)
        resultado.append({"nombre": op.nombre, "comparacion_texto": texto, "comparacion_color": color})
    return resultado


# ══════════════════════ AGRUPACIÓN PARA EL LAYOUT ══════════════════════

def agrupar_por_seccion(metricas: list[Metrica]) -> list[tuple[str, list[Metrica], list[Metrica]]]:
    """Agrupa métricas por seccion_ppt, preservando el orden de aparición
    en la lista (que define el orden visual). Retorna
    (seccion, metricas_normales, metricas_destacadas). Ignora métricas
    sin seccion_ppt (no van al PPT)."""
    normales: dict[str, list[Metrica]] = {}
    destacadas: dict[str, list[Metrica]] = {}
    orden: list[str] = []
    for m in metricas:
        if not m.seccion_ppt:
            continue
        if m.seccion_ppt not in normales:
            normales[m.seccion_ppt] = []
            destacadas[m.seccion_ppt] = []
            orden.append(m.seccion_ppt)
        if m.destacado_ppt:
            destacadas[m.seccion_ppt].append(m)
        else:
            normales[m.seccion_ppt].append(m)
    return [(seccion, normales[seccion], destacadas[seccion]) for seccion in orden]


def agrupar_items_de_seccion(metricas_seccion: list[Metrica]) -> list[dict]:
    """
    Convierte la lista plana de métricas de una sección en 'items' para
    dibujar, preservando el orden. Cada item es:
      {'tipo': 'simple', 'metrica': Metrica}
      {'tipo': 'grupo', 'etiqueta': str, 'metricas': [Metrica, ...]}
    """
    items: list[dict] = []
    grupos_por_etiqueta: dict[str, dict] = {}
    for m in metricas_seccion:
        if m.grupo_visual_ppt:
            if m.grupo_visual_ppt in grupos_por_etiqueta:
                grupos_por_etiqueta[m.grupo_visual_ppt]["metricas"].append(m)
            else:
                item = {"tipo": "grupo", "etiqueta": m.grupo_visual_ppt, "metricas": [m]}
                grupos_por_etiqueta[m.grupo_visual_ppt] = item
                items.append(item)
        else:
            items.append({"tipo": "simple", "metrica": m})
    return items


# ══════════════════════ FUNCIÓN PRINCIPAL ══════════════════════

def obtener_datos_para_ppt(entidad_nombre: str, entidad_nombre_archivo: str, fecha: str) -> dict:
    """
    Retorna:
    {
      'secciones': [(nombre_seccion, [items], [destacados]), ...],
      'fecha_anterior_encontrada': bool,
    }
    Cada item/destacado trae 'dato' (comparación + cumplimiento) y, si
    aplica, 'operaciones' (subconteos tipo IOS/Android).
    """
    repo = MetricaRepository()
    metricas = sorted(repo.listar(), key=lambda m: m.orden_ppt)

    carpeta_actual = OUTPUT_DIR / fecha
    ruta_reporte_actual = carpeta_actual / f"{entidad_nombre_archivo}.xlsx"
    ruta_cumplimiento_actual = carpeta_actual / f"resumen_cumplimiento_{entidad_nombre.lower()}.xlsx"

    ruta_reporte_anterior = buscar_archivo_anterior(entidad_nombre_archivo, fecha)
    ruta_cumplimiento_anterior = buscar_archivo_anterior(
        f"resumen_cumplimiento_{entidad_nombre.lower()}", fecha)

    cumplimiento_actual = cargar_cumplimiento(ruta_cumplimiento_actual)
    cumplimiento_anterior = cargar_cumplimiento(ruta_cumplimiento_anterior)

    def _con_dato(m: Metrica) -> dict:
        dato = construir_dato_metrica(m, cumplimiento_actual, cumplimiento_anterior)
        resultado = {"metrica": m, "dato": dato}
        if m.operaciones_ppt:
            resultado["operaciones"] = construir_operaciones_metrica(
                m, ruta_reporte_actual, ruta_reporte_anterior)
        return resultado

    secciones_resultado = []
    for nombre_seccion, metricas_normales, metricas_destacadas in agrupar_por_seccion(metricas):
        items_crudos = agrupar_items_de_seccion(metricas_normales)
        items_final = []
        for item in items_crudos:
            if item["tipo"] == "simple":
                items_final.append({"tipo": "simple", **_con_dato(item["metrica"])})
            else:
                sub = [_con_dato(m) for m in item["metricas"]]
                items_final.append({"tipo": "grupo", "etiqueta": item["etiqueta"], "items": sub})

        destacados_final = [_con_dato(m) for m in metricas_destacadas]
        secciones_resultado.append((nombre_seccion, items_final, destacados_final))

    return {
        "secciones": secciones_resultado,
        "fecha_anterior_encontrada": ruta_cumplimiento_anterior is not None,
    }