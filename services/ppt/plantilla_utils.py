"""Utilidades base para el motor de plantillas: leer hojas de un Excel,
comparar dos semanas, y encontrar banderas <<...>> en un texto. Puerto
de ppt_utils.py del sistema original — misma lógica de colores.
"""
import re
import pandas as pd
from pptx.dml.color import RGBColor


def leer_hojas_excel(ruta_excel: str) -> dict:
    """Lee todas las hojas de un Excel (excepto las que empiezan con
    'Resumen') y retorna {hoja: num_filas}."""
    hojas = {}
    try:
        xl = pd.ExcelFile(ruta_excel)
        for hoja in xl.sheet_names:
            if not hoja.startswith("Resumen"):
                df = xl.parse(hoja)
                hojas[hoja] = len(df)
    except Exception as e:
        print(f"   ❌ Error leyendo {ruta_excel}: {e}")
    return hojas


def formato_cambio(n_actual: int, n_anterior: int) -> tuple:
    """
    Retorna (texto_formateado, color_rgb, es_aumento). Misma lógica que
    el sistema original:
    - Si n_actual != 0: cualquier diferencia (subida o bajada) se marca
      en rojo (llamar la atención sobre incumplimientos activos).
    - Si n_actual == 0: siempre azul, sin importar si hubo cambio.
    """
    diferencia = n_actual - n_anterior

    if n_actual != 0:
        if diferencia > 0:
            simbolo, es_aumento = "↑", True
        elif diferencia < 0:
            simbolo, es_aumento = "↓", False
        else:
            simbolo, es_aumento = "=", None
        color = RGBColor(192, 0, 0)
        texto = f"{simbolo} {n_actual} con respecto a la semana pasada ({n_anterior})"
        return texto, color, es_aumento

    simbolo = "↑" if diferencia > 0 else ("↓" if diferencia < 0 else "=")
    color = RGBColor(0, 112, 192)
    texto = f"{simbolo} {n_actual} sin cambios respecto a la semana pasada ({n_anterior})"
    return texto, color, None


def comparar_excel(hojas_actual: dict, hojas_anterior: dict) -> dict:
    """{hoja: num_filas} x2 -> {hoja: {actual, anterior, diferencia, texto, color}}."""
    resultado = {}
    for hoja, n_actual in hojas_actual.items():
        n_ant = hojas_anterior.get(hoja, 0)
        texto_fmt, color, _ = formato_cambio(n_actual, n_ant)
        resultado[hoja] = {
            "actual": n_actual, "anterior": n_ant,
            "diferencia": n_actual - n_ant,
            "texto": texto_fmt, "color": color,
        }
    return resultado


def buscar_bandera(text) -> list:
    """Busca banderas tipo <<bandera>> en el texto."""
    if not text:
        return []
    return re.findall(r"<<(.*?)>>", text)