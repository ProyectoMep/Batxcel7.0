"""Modelo Observacion: tareas o comentarios de seguimiento que aparecen
en el acta. Igual que Asistente, se persiste por entidad y siempre es
editable — el acta nueva parte de lo último que dejaste guardado.
"""
from dataclasses import dataclass
from pathlib import Path
from config.settings import DATA_DIR
from models.json_repository import JsonRepository


@dataclass
class Observacion:
    id: int | None = None
    texto: str = ""


def observacion_desde_dict(d: dict) -> Observacion:
    return Observacion(id=d.get("id"), texto=d.get("texto", ""))


def observacion_a_dict(o: Observacion) -> dict:
    return {"id": o.id, "texto": o.texto}


class ObservacionRepository(JsonRepository):
    def __init__(self, entidad_nombre: str):
        ruta = DATA_DIR / f"observaciones_{entidad_nombre.lower()}.json"
        super().__init__(ruta_archivo=ruta, factory=observacion_desde_dict, to_dict=observacion_a_dict)