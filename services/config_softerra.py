"""Configuración del paso 'softerra': qué CSV de directorio se
concatenan, qué columnas se toman, y cómo se renombran. Se persiste en
un único JSON (no es una lista de registros, es una configuración
singular), editable a mano si hace falta. Reemplaza config/softerra.json
del sistema original.
"""
import json
from config.settings import DATA_DIR

_RUTA = DATA_DIR / "config_softerra.json"

_DEFECTO = {
    "fuentes": [
        {"patron": "PCR.csv"},
        {"patron": "SBI.csv"},
        {"patron": "SEC.csv"},
        {"patron": "SNC.csv"},
        {"patron": "UNC.csv"},
        {"patron": "CO2.csv"},
    ],
    "skiprows": [1],
    "columnas": ["name", "company", "countryCode", "description",
                "displayName", "employeeNumber", "mail", "title"],
    "renombrar": {"company": "company_softerra"},
    "salida": "softerra.xlsx",
}


def cargar_config_softerra() -> dict:
    if not _RUTA.exists():
        _RUTA.parent.mkdir(parents=True, exist_ok=True)
        with open(_RUTA, "w", encoding="utf-8") as f:
            json.dump(_DEFECTO, f, ensure_ascii=False, indent=2)
        return dict(_DEFECTO)
    with open(_RUTA, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_config_softerra(config: dict) -> None:
    _RUTA.parent.mkdir(parents=True, exist_ok=True)
    with open(_RUTA, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)