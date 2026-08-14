"""Calcula las banderas <<...>> que corresponden a cada métrica, para
mostrarlas al usuario (qué debe escribir en la plantilla PowerPoint) y
para saber qué valores inyectar al generar la presentación. Replica el
esquema de banderas del sistema original (ppt_core.py / ppt_bandera_handler.py),
pero sin necesitar el diccionario de mapeo manual: aquí el nombre de la
hoja del reporte y el nombre en cumplimiento son siempre el mismo
(Metrica.nombre).
"""
import re
from models.metrica import Metrica


def normalizar_clave(nombre: str) -> str:
    """Convierte 'Push security' -> 'push_security', igual que el
    sistema original (minúsculas, espacios/guiones/puntos -> _)."""
    return re.sub(r"[\s\-\.]+", "_", nombre.strip().lower())


def banderas_de_metrica(metrica: Metrica) -> list[dict]:
    """Retorna [{'bandera': str, 'descripcion': str}, ...] — las banderas
    <<...>> que esta métrica puede llenar en una plantilla PPT."""
    clave = normalizar_clave(metrica.nombre)
    banderas = []

    if metrica.incluir_en_reporte:
        banderas.append({
            "bandera": clave,
            "descripcion": "Comparación semanal, ej: '↑ 5 con respecto a la semana pasada (3)'",
        })

    if metrica.cumplimiento.aplica:
        banderas.extend([
            {"bandera": f"{clave}_cumplimiento", "descripcion": "Texto combinado, ej: '98.8% / Cumple'"},
            {"bandera": f"{clave}_status", "descripcion": "'Cumple' o 'No Cumple'"},
            {"bandera": f"{clave}_umbral", "descripcion": "Umbral aceptable, ej: '97%'"},
            {"bandera": f"{clave}_numerador", "descripcion": "Numerador del cumplimiento"},
            {"bandera": f"{clave}_denominador", "descripcion": "Denominador del cumplimiento"},
        ])

    for op in metrica.operaciones_ppt:
        clave_hoja = normalizar_clave(op.hoja_fuente)
        banderas.append({
            "bandera": f"{clave_hoja}({op.nombre})",
            "descripcion": f"Subconteo '{op.nombre}', calculado sobre la hoja '{op.hoja_fuente}'",
        })

    return banderas


def todas_las_banderas(metricas: list[Metrica]) -> list[dict]:
    """{'metrica': nombre, 'banderas': [...]} para todas las métricas
    que producen al menos una bandera."""
    resultado = []
    for m in metricas:
        banderas = banderas_de_metrica(m)
        if banderas:
            resultado.append({"metrica": m.nombre, "banderas": banderas})
    return resultado