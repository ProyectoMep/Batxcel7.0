"""Encuentra el archivo real en input/ que corresponde al patrón de una
métrica. Si no está en input/ y la métrica tiene un patrón de respaldo,
busca en templates_maestros/maestros/. Si hay varias coincidencias,
retorna la modificada más recientemente (igual que el sistema original).
"""
from pathlib import Path
from config.settings import INPUT_DIR, TEMPLATES_MAESTROS_DIR


def resolver_archivo_por_patron(patron: str, carpeta: Path = None) -> Path | None:
    """Busca 'patron' (glob) dentro de 'carpeta' (por defecto INPUT_DIR).
    Retorna el Path más reciente si hay varias coincidencias, o None."""
    if not patron:
        return None
    carpeta = carpeta or INPUT_DIR
    coincidencias = [p for p in carpeta.glob(patron) if p.is_file()]
    if not coincidencias:
        return None
    return max(coincidencias, key=lambda p: p.stat().st_mtime)


def resolver_archivo_de_metrica(metrica) -> tuple[Path | None, bool]:
    """
    Resuelve el archivo de una Metrica siguiendo la prioridad:
    1) input/ según archivo_patron
    2) templates_maestros/maestros/ según archivo_respaldo_patron (si existe)
    Retorna (ruta, es_respaldo). ruta es None si no se encontró en ningún lado.
    """
    ruta = resolver_archivo_por_patron(metrica.archivo_patron, INPUT_DIR)
    if ruta is not None:
        return ruta, False

    if metrica.archivo_respaldo_patron:
        ruta_resp = resolver_archivo_por_patron(metrica.archivo_respaldo_patron, TEMPLATES_MAESTROS_DIR)
        if ruta_resp is not None:
            return ruta_resp, True

    return None, False


def verificar_archivos_metricas(metricas: list) -> dict:
    """
    Revisa todas las métricas obligatorias y retorna:
    {'encontrados': {nombre_metrica: nombre_archivo}, 'faltantes': [nombres]}
    Una métrica con respaldo disponible NO cuenta como faltante.
    """
    encontrados, faltantes = {}, []
    for metrica in metricas:
        if not metrica.obligatoria:
            continue
        ruta, _ = resolver_archivo_de_metrica(metrica)
        if ruta is not None:
            encontrados[metrica.nombre] = ruta.name
        else:
            faltantes.append(metrica.nombre)
    return {"encontrados": encontrados, "faltantes": faltantes}