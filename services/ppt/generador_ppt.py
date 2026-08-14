"""Orquesta la generación de presentaciones: resuelve la plantilla de la
entidad, llama a ppt_core (que reemplaza las banderas), exporta a PDF
(best-effort, requiere PowerPoint instalado vía COM) y guarda un JSON
al lado del .pptx con la metadata de qué semanas se compararon —eso lo
usa después el módulo de Actas. Puerto de presentacion.py del sistema
original.
"""
import json
import re
from pathlib import Path

from config.settings import OUTPUT_DIR, TEMPLATES_PPT_DIR
from models.metrica import MetricaRepository
from models.entidad import EntidadRepository
from services.ppt.ppt_core import generar_ppt_comparativo


def fechas_disponibles(entidad_nombre: str) -> list[str]:
    """Fechas del histórico (más reciente primero) que tienen el reporte
    de esta entidad ya generado."""
    repo = EntidadRepository()
    entidad = repo.obtener_por_nombre(entidad_nombre)
    if entidad is None:
        return []
    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre
    fechas = []
    if OUTPUT_DIR.exists():
        for carpeta in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if carpeta.is_dir() and (carpeta / f"{nombre_archivo}.xlsx").exists():
                fechas.append(carpeta.name)
    return fechas


def listar_presentaciones() -> dict:
    """{entidad: [{fecha, nombre, pptx, pdf}]} recorriendo todo el histórico."""
    repo = EntidadRepository()
    entidades = repo.listar()
    resultado = {e.nombre: [] for e in entidades}
    if not OUTPUT_DIR.exists():
        return resultado
    for carpeta in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not carpeta.is_dir():
            continue
        for entidad in entidades:
            sub = carpeta / "presentaciones" / entidad.nombre
            if not sub.is_dir():
                continue
            for f in sorted(sub.glob("*.pptx")):
                pdf = f.with_suffix(".pdf")
                resultado[entidad.nombre].append({
                    "fecha": carpeta.name,
                    "nombre": f.stem,
                    "pptx": f"presentaciones/{entidad.nombre}/{f.name}",
                    "pdf": f"presentaciones/{entidad.nombre}/{pdf.name}" if pdf.exists() else None,
                })
    return resultado


def _exportar_pdf(ruta_pptx: Path) -> Path | None:
    """Exporta el pptx a PDF usando PowerPoint (COM, solo Windows con
    Office instalado). Si no es posible, retorna None sin fallar —
    el .pptx se guarda igual."""
    try:
        import comtypes.client
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        try:
            pres = powerpoint.Presentations.Open(str(ruta_pptx.resolve()), WithWindow=False)
            ruta_pdf = ruta_pptx.with_suffix(".pdf")
            pres.SaveAs(str(ruta_pdf.resolve()), 32)  # 32 = ppSaveAsPDF
            pres.Close()
            return ruta_pdf
        finally:
            powerpoint.Quit()
    except Exception as e:
        print(f"   ⚠️  No se pudo exportar a PDF: {e}")
        return None


def generar_presentacion(entidad_nombre: str, fecha_actual: str, fecha_anterior: str = None,
                         nombre: str = None) -> dict:
    """Genera el .pptx (y su copia .pdf si es posible) comparando
    fecha_actual vs fecha_anterior. El cumplimiento siempre es el de
    fecha_actual (misma carpeta = mismo corte)."""
    repo_entidad = EntidadRepository()
    entidad = repo_entidad.obtener_por_nombre(entidad_nombre)
    if entidad is None:
        return {"ok": False, "error": f"No existe la entidad '{entidad_nombre}'"}

    if not entidad.plantilla_ppt:
        return {"ok": False,
                "error": f"La entidad '{entidad_nombre}' no tiene plantilla PPT configurada "
                         f"(campo 'plantilla_ppt' vacío)"}

    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre
    fechas = fechas_disponibles(entidad_nombre)
    if fecha_actual not in fechas:
        return {"ok": False, "error": f"No hay reporte de {entidad_nombre} en la fecha {fecha_actual}"}

    if not fecha_anterior:
        anteriores = [f for f in fechas if f < fecha_actual]
        if not anteriores:
            return {"ok": False,
                    "error": f"No existe un reporte anterior a {fecha_actual} para comparar"}
        fecha_anterior = anteriores[0]
    elif fecha_anterior not in fechas:
        return {"ok": False, "error": f"No hay reporte de {entidad_nombre} en la fecha {fecha_anterior}"}
    if fecha_anterior >= fecha_actual:
        return {"ok": False, "error": "La fecha anterior debe ser menor que la actual"}

    carpeta_actual = OUTPUT_DIR / fecha_actual
    ruta_excel_actual = carpeta_actual / f"{nombre_archivo}.xlsx"
    ruta_excel_anterior = OUTPUT_DIR / fecha_anterior / f"{nombre_archivo}.xlsx"
    ruta_cumplimiento = carpeta_actual / f"resumen_cumplimiento_{entidad.nombre.lower()}.xlsx"
    ruta_plantilla = TEMPLATES_PPT_DIR / entidad.plantilla_ppt

    if not ruta_plantilla.exists():
        return {"ok": False,
                "error": f"Plantilla no encontrada: {ruta_plantilla}. "
                         f"Colócala en templates_maestros/ppt/{entidad.plantilla_ppt}"}
    if not ruta_cumplimiento.exists():
        return {"ok": False, "error": f"Falta el archivo de cumplimiento de {fecha_actual}"}

    nombre = (nombre or f"Presentacion_{entidad.nombre}_{fecha_actual}").strip()
    nombre = re.sub(r'[\\/:*?"<>|]+', "_", nombre)

    carpeta_ppt = carpeta_actual / "presentaciones" / entidad.nombre
    carpeta_ppt.mkdir(parents=True, exist_ok=True)
    ruta_salida = carpeta_ppt / f"{nombre}.pptx"

    metricas = MetricaRepository().listar()
    generar_ppt_comparativo(ruta_excel_actual, ruta_excel_anterior, ruta_plantilla,
                            ruta_salida, metricas, ruta_resumen_cumplimiento=ruta_cumplimiento)

    ruta_pdf = _exportar_pdf(ruta_salida)

    # Metadatos para el módulo de actas (contra qué fecha se comparó)
    meta = {"entidad": entidad.nombre, "fecha_actual": fecha_actual,
            "fecha_anterior": fecha_anterior, "nombre": nombre}
    with open(ruta_salida.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return {"ok": True, "entidad": entidad.nombre, "fecha_actual": fecha_actual,
            "fecha_anterior": fecha_anterior, "pptx": ruta_salida.name,
            "pdf": ruta_pdf.name if ruta_pdf else None}