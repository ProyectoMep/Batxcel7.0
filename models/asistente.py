"""Modelo Asistente: lista de personas que asisten al acta de
seguimiento. Se persiste por entidad (un archivo por BSNC/SF), y es
siempre editable desde la interfaz — no se reconstruye desde ningún
.docx, así que el acta nueva siempre parte de la última lista que
dejaste guardada.
"""
from dataclasses import dataclass
from pathlib import Path
from config.settings import DATA_DIR
from models.json_repository import JsonRepository


@dataclass
class Asistente:
    id: int | None = None
    nombre: str = ""
    cargo: str = ""
    estado: str = "Asistió"


def asistente_desde_dict(d: dict) -> Asistente:
    return Asistente(id=d.get("id"), nombre=d.get("nombre", ""), cargo=d.get("cargo", ""),
                     estado=d.get("estado", "Asistió"))


def asistente_a_dict(a: Asistente) -> dict:
    return {"id": a.id, "nombre": a.nombre, "cargo": a.cargo, "estado": a.estado}


class AsistenteRepository(JsonRepository):
    def __init__(self, entidad_nombre: str):
        ruta = DATA_DIR / f"asistentes_{entidad_nombre.lower()}.json"
        super().__init__(ruta_archivo=ruta, factory=asistente_desde_dict, to_dict=asistente_a_dict)