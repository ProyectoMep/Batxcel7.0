"""Extrae asistentes y observaciones de un acta .docx existente (la
tuya real, o cualquiera generada por este mismo sistema), para poblar
los JSON editables. Esto es lo que te permite decir 'coloca tu acta
real en output/ y el sistema la usa como base' — solo hace falta
importarla una vez; de ahí en adelante, como cada generación nueva
EDITA ese mismo documento (ver generador_acta.py), el 'último generado'
siempre está disponible sin tener que reimportar.
"""
from pathlib import Path
from docx import Document

from config.settings import OUTPUT_DIR
from services.acta.estructura_docx import tabla_participantes, tabla_observaciones


def buscar_ultima_acta(entidad_nombre: str) -> Path | None:
    """Busca en output/*/actas/<entidad>/ el .docx más reciente (por
    fecha de carpeta, luego por fecha de modificación)."""
    if not OUTPUT_DIR.exists():
        return None
    candidatos = []
    for carpeta in OUTPUT_DIR.iterdir():
        if not carpeta.is_dir():
            continue
        sub = carpeta / "actas" / entidad_nombre
        if not sub.is_dir():
            continue
        for f in sub.glob("*.docx"):
            candidatos.append((carpeta.name, f.stat().st_mtime, f))
    if not candidatos:
        return None
    candidatos.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return candidatos[0][2]


def extraer_asistentes(ruta_docx: Path) -> list[dict]:
    doc = Document(ruta_docx)
    tabla = tabla_participantes(doc)
    if tabla is None:
        return []
    resultado = []
    for row in tabla.rows[1:]:
        celdas = [c.text.strip() for c in row.cells]
        if not celdas or not celdas[0]:
            continue
        resultado.append({
            "nombre": celdas[0],
            "cargo": celdas[1] if len(celdas) > 1 else "",
            "estado": celdas[2] if len(celdas) > 2 else "Asistió",
        })
    return resultado


def extraer_observaciones(ruta_docx: Path) -> list[str]:
    doc = Document(ruta_docx)
    tabla = tabla_observaciones(doc)
    if tabla is None:
        return []
    resultado = []
    for row in tabla.rows:
        texto = row.cells[0].text.strip().lstrip("•").lstrip("-").strip()
        if texto:
            resultado.append(texto)
    return resultado


def importar_desde_acta(entidad_nombre: str, ruta_docx: Path = None) -> dict:
    """Si no se pasa ruta_docx explícita, busca la última acta generada
    para esa entidad. Retorna {'ok', 'asistentes': [...], 'observaciones': [...], 'archivo': str}."""
    ruta = ruta_docx or buscar_ultima_acta(entidad_nombre)
    if ruta is None or not ruta.exists():
        return {"ok": False, "error": "No se encontró ninguna acta anterior para importar"}

    asistentes = extraer_asistentes(ruta)
    observaciones = extraer_observaciones(ruta)

    return {"ok": True, "archivo": ruta.name,
            "asistentes": asistentes, "observaciones": observaciones}