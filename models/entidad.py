"""Modelo Entidad: representa una unidad de negocio (BSNC, SF) y la
lista de identificadores de texto que permiten reconocerla dentro de
las columnas de 'company' de cada archivo. Reemplaza la mitad de
separacion.json del sistema original."""
from dataclasses import dataclass, field
from pathlib import Path
from config.settings import DATA_DIR
from models.json_repository import JsonRepository


@dataclass
class Entidad:
    id: int | None = None
    nombre: str = ""                         # ej. "BSNC", "SF"
    nombre_archivo_salida: str = ""           # ej. "Resumen Cyber BSNC"
    identificadores: list[str] = field(default_factory=list)  # ej. ["BS de Negocios Colombia", "SNC", ...]
    plantilla_ppt: str = ""                   # nombre del .pptx dentro de templates_maestros/ppt/
    tema_acta: str = ""                       # texto fijo de "Tema" en la sección 1 del acta
    objetivo_acta: str = ""                   # texto fijo de "Objetivo" en la sección 1 del acta


def entidad_desde_dict(d: dict) -> Entidad:
    return Entidad(
        id=d.get("id"),
        nombre=d.get("nombre", ""),
        nombre_archivo_salida=d.get("nombre_archivo_salida", ""),
        identificadores=list(d.get("identificadores", [])),
        plantilla_ppt=d.get("plantilla_ppt", ""),
        tema_acta=d.get("tema_acta", ""),
        objetivo_acta=d.get("objetivo_acta", ""),
    )


def entidad_a_dict(e: Entidad) -> dict:
    return {
        "id": e.id,
        "nombre": e.nombre,
        "nombre_archivo_salida": e.nombre_archivo_salida,
        "identificadores": e.identificadores,
        "plantilla_ppt": e.plantilla_ppt,
        "tema_acta": e.tema_acta,
        "objetivo_acta": e.objetivo_acta,
    }


class EntidadRepository(JsonRepository):
    def __init__(self, ruta: Path = None):
        super().__init__(
            ruta_archivo=ruta or (DATA_DIR / "entidades.json"),
            factory=entidad_desde_dict,
            to_dict=entidad_a_dict,
        )

    def obtener_por_nombre(self, nombre: str):
        for e in self.listar():
            if e.nombre.strip().lower() == nombre.strip().lower():
                return e
        return None