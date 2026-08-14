"""Modelo FilaActa: define cada fila de la tabla de métricas del acta —
qué hoja (o hoja+operación) leer para calcular la tendencia, y qué texto
de 'Acción a desarrollar' usar según si hay o no equipos/usuarios que
gestionar esta semana.
"""
from dataclasses import dataclass
from pathlib import Path
from config.settings import DATA_DIR
from models.json_repository import JsonRepository


@dataclass
class FilaActa:
    id: int | None = None
    orden: int = 0
    metrica_acta: str = ""              # nombre que se muestra en la tabla del acta
    hoja: str = ""                      # nombre real de la métrica/hoja del reporte
    operacion: str | None = None        # nombre de la operación (ej. 'IOS'), o None para conteo directo
    accion_con_gestion: str = ""        # texto cuando el conteo actual es > 0
    accion_sin_gestion: str = "No hay acción que gestionar"  # cuando el conteo actual es 0
    # Texto fijo que sigue después de la palabra de tendencia, ej.
    # "la cantidad de workstations sin la herramienta habilitada con
    # respecto a la semana pasada." -> se arma como
    # f"{palabra} {descripcion_sufijo}" = "Se mantuvo la cantidad..."
    descripcion_sufijo: str = ""
    # Definición de la métrica para la tabla de Glosario al final del acta.
    glosario: str = ""


def fila_acta_desde_dict(d: dict) -> FilaActa:
    return FilaActa(
        id=d.get("id"),
        orden=d.get("orden", 0),
        metrica_acta=d.get("metrica_acta", ""),
        hoja=d.get("hoja", ""),
        operacion=d.get("operacion"),
        accion_con_gestion=d.get("accion_con_gestion", ""),
        accion_sin_gestion=d.get("accion_sin_gestion", "No hay acción que gestionar"),
        descripcion_sufijo=d.get("descripcion_sufijo", ""),
        glosario=d.get("glosario", ""),
    )


def fila_acta_a_dict(f: FilaActa) -> dict:
    return {
        "id": f.id,
        "orden": f.orden,
        "metrica_acta": f.metrica_acta,
        "hoja": f.hoja,
        "operacion": f.operacion,
        "accion_con_gestion": f.accion_con_gestion,
        "accion_sin_gestion": f.accion_sin_gestion,
        "descripcion_sufijo": f.descripcion_sufijo,
        "glosario": f.glosario,
    }


class FilaActaRepository(JsonRepository):
    def __init__(self, ruta: Path = None):
        super().__init__(
            ruta_archivo=ruta or (DATA_DIR / "filas_acta.json"),
            factory=fila_acta_desde_dict,
            to_dict=fila_acta_a_dict,
        )

    def ordenadas(self) -> list[FilaActa]:
        return sorted(self.listar(), key=lambda f: f.orden)