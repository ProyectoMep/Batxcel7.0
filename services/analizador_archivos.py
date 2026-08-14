"""Lee un archivo subido desde el formulario de Métricas y devuelve sus
columnas + un patrón de nombre sugerido (reemplazando fechas por *)."""
import re
import tempfile
from pathlib import Path
from services.lector import leer_excel_o_csv


def analizar_archivo_subido(file_storage) -> dict:
    """
    file_storage: objeto de Flask (request.files['archivo']).
    Retorna {'columnas': [...], 'nombre_archivo_original': str, 'patron_sugerido': str}
    """
    sufijo = Path(file_storage.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
        file_storage.save(tmp.name)
        ruta_tmp = Path(tmp.name)

    try:
        df = leer_excel_o_csv(ruta_tmp, solo_encabezados=True)
        columnas = list(df.columns) if df is not None else []
    finally:
        ruta_tmp.unlink(missing_ok=True)

    return {
        "columnas": columnas,
        "nombre_archivo_original": file_storage.filename,
        "patron_sugerido": _sugerir_patron(file_storage.filename),
    }


def _sugerir_patron(nombre_archivo: str) -> str:
    """Reemplaza fragmentos de fecha típicos (2026-06-29, 6-30-2026,
    _0ac57aea-..., etc.) por '*' para que el patrón sirva semana a semana."""
    patron = nombre_archivo
    patron = re.sub(r"\d{4}-\d{2}-\d{2}", "*", patron)
    patron = re.sub(r"\d{1,2}-\d{1,2}-\d{4}", "*", patron)
    patron = re.sub(r"_[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}", "_*", patron)
    patron = re.sub(r"_\d{6,}", "_*", patron)
    if "*" not in patron:
        # Sin patrón fecha detectado: al menos deja el nombre tal cual
        # (el usuario puede editarlo manualmente para agregar el *).
        pass
    return patron