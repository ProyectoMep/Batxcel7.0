"""Calcula las tendencias (▲ Aumentó / ▼ Disminuyó / ● Se mantuvo) de
cada fila del acta, comparando el reporte actual contra el anterior.
Reutiliza el mismo mecanismo de lectura de hojas y operaciones que ya
construimos para las banderas del PPT — una operación (ej. 'IOS' dentro
de 'Moviles Compliant') es exactamente el mismo concepto aquí.
"""
from pathlib import Path
import pandas as pd

from config.settings import OUTPUT_DIR
from models.metrica import MetricaRepository
from models.entidad import EntidadRepository
from models.fila_acta import FilaActaRepository
from services.reglas import evaluar_grupos
from services.ppt.plantilla_utils import leer_hojas_excel
from services.ppt.banderas import normalizar_clave

ROJO = (0xC6, 0x28, 0x28)      # Aumentó (malo)
VERDE = (0x2E, 0x7D, 0x32)     # Disminuyó (bueno)
GRIS = (0x55, 0x55, 0x55)      # Se mantuvo


def _construir_indice_operaciones(metricas) -> dict:
    """{'hoja_normalizada': [{'nombre': str, 'condicion': [[Condicion]]}]}."""
    indice: dict[str, list] = {}
    for m in metricas:
        for op in m.operaciones_ppt:
            clave_hoja = normalizar_clave(op.hoja_fuente)
            indice.setdefault(clave_hoja, []).append({"nombre": op.nombre, "condicion": op.condicion})
    return indice


def _leer_hoja_normalizada(ruta_excel, hoja_normalizada: str) -> pd.DataFrame | None:
    if ruta_excel is None or not Path(ruta_excel).exists():
        return None
    try:
        xl = pd.ExcelFile(ruta_excel)
    except Exception:
        return None
    for hoja in xl.sheet_names:
        if normalizar_clave(hoja) == hoja_normalizada:
            try:
                return xl.parse(hoja)
            except Exception:
                return None
    return None


def _contar_operacion(ruta_excel, hoja_normalizada: str, operacion_nombre: str,
                      operaciones_index: dict) -> int | None:
    ops = operaciones_index.get(hoja_normalizada, [])
    op = next((o for o in ops if o["nombre"].lower() == operacion_nombre.lower()), None)
    if op is None:
        return None
    df = _leer_hoja_normalizada(ruta_excel, hoja_normalizada)
    if df is None:
        return None
    return int(evaluar_grupos(df, op["condicion"]).sum())


def _tendencia(actual: int | None, anterior: int | None) -> tuple[str, str, tuple]:
    """Retorna (texto, palabra, color_rgb)."""
    if actual is None or anterior is None:
        return "● Se mantuvo", "Se mantuvo", GRIS
    if actual > anterior:
        return "▲ Aumentó", "Aumentó", ROJO
    if actual < anterior:
        return "▼ Disminuyó", "Disminuyó", VERDE
    return "● Se mantuvo", "Se mantuvo", GRIS


def calcular_tendencias(entidad_nombre: str, fecha_actual: str, fecha_anterior: str) -> list[dict]:
    """
    Retorna una lista ordenada de:
    {'metrica_acta', 'actual', 'anterior', 'tendencia', 'palabra',
     'color', 'accion'}
    """
    entidad_repo = EntidadRepository()
    entidad = entidad_repo.obtener_por_nombre(entidad_nombre)
    if entidad is None:
        return []

    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre
    ruta_actual = OUTPUT_DIR / fecha_actual / f"{nombre_archivo}.xlsx"
    ruta_anterior = OUTPUT_DIR / fecha_anterior / f"{nombre_archivo}.xlsx"

    hojas_actual = leer_hojas_excel(str(ruta_actual))
    hojas_anterior = leer_hojas_excel(str(ruta_anterior))

    metricas = MetricaRepository().listar()
    operaciones_index = _construir_indice_operaciones(metricas)

    filas_cfg = FilaActaRepository().ordenadas()
    resultado = []

    for fila in filas_cfg:
        if fila.operacion:
            clave_hoja = normalizar_clave(fila.hoja)
            actual = _contar_operacion(ruta_actual, clave_hoja, fila.operacion, operaciones_index)
            anterior = _contar_operacion(ruta_anterior, clave_hoja, fila.operacion, operaciones_index)
        else:
            actual = hojas_actual.get(fila.hoja)
            anterior = hojas_anterior.get(fila.hoja)

        texto, palabra, color = _tendencia(actual, anterior)
        hay_gestion = (actual or 0) > 0
        accion = fila.accion_con_gestion if hay_gestion else fila.accion_sin_gestion
        descripcion = f"{palabra} {fila.descripcion_sufijo}".strip()

        resultado.append({
            "metrica_acta": fila.metrica_acta,
            "actual": actual, "anterior": anterior,
            "tendencia": texto, "palabra": palabra, "color": color,
            "accion": accion, "descripcion": descripcion,
        })

    return resultado