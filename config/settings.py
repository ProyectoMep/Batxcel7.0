"""Rutas del proyecto. Aquí NO va configuración de negocio (eso vive en models/data).
Todas las rutas se calculan desde la ubicación de este archivo, así que
el proyecto corre igual sin importar en qué carpeta o equipo esté."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR              = BASE_DIR / "input"
OUTPUT_DIR             = BASE_DIR / "output"
PROCESADOS_DIR         = BASE_DIR / "procesados"
DATA_DIR               = BASE_DIR / "data"
TEMPLATES_MAESTROS_DIR = BASE_DIR / "templates_maestros" / "maestros"
TEMPLATES_DOCX_DIR     = BASE_DIR / "templates_docx"
TEMPLATES_PPT_DIR      = BASE_DIR / "templates_maestros" / "ppt"

for carpeta in (INPUT_DIR, OUTPUT_DIR, PROCESADOS_DIR, DATA_DIR, TEMPLATES_PPT_DIR):
    carpeta.mkdir(parents=True, exist_ok=True)