"""Modelo Metrica: representa toda la configuración de una métrica de
cumplimiento (antes repartida en reportes.json, cumplimiento.json,
enriquecimiento.json, limpieza.json y separacion.json). Se persiste en
data/metricas.json a través de MetricaRepository.
"""
from dataclasses import dataclass, field, asdict
from pathlib import Path
from config.settings import DATA_DIR
from models.json_repository import JsonRepository

OPERADORES_VALIDOS = ("igual", "distinto", "contiene", "no_contiene", "vacio", "no_vacio")


@dataclass
class Condicion:
    columna: str
    operador: str      # uno de OPERADORES_VALIDOS
    valor: str = ""     # no aplica para 'vacio' / 'no_vacio'

    def __post_init__(self):
        if self.operador not in OPERADORES_VALIDOS:
            raise ValueError(f"Operador inválido: {self.operador}")


@dataclass
class Enriquecimiento:
    archivo_patron: str          # patrón del archivo con el que se cruza
    columna_base: str            # columna en la métrica actual
    columna_cruzar: str          # columna en el archivo externo
    columnas_extraer: list[str] = field(default_factory=list)
    # Texto a quitar de columna_base ANTES de cruzar (ej. "@dominio.com"),
    # solo para este cruce puntual — no afecta los datos finales, solo
    # la llave usada para encontrar coincidencias. Necesario cuando el
    # archivo externo usa el usuario sin dominio (ej. sistemas de RRHH)
    # mientras que la columna base sí lo tiene (ej. exports de Entra/AD).
    texto_a_quitar_del_base: str | None = None


@dataclass
class ConfigCumplimiento:
    aplica: bool = False
    operador: str = ">"          # ">" o "<"
    umbral: float = 0.97
    criterio_favor: list[list[Condicion]] = field(default_factory=list)
    criterio_total: list[list[Condicion]] = field(default_factory=list)
    criterio_total_fijo: int | None = None
    excluir: list[list[Condicion]] = field(default_factory=list)


@dataclass
class OperacionPPT:
    """Subconteo dentro del PPT (ej. IOS/Android dentro de 'Update'):
    cuenta filas de la hoja 'hoja_fuente' (otra métrica que sí genera
    hoja en el reporte) que cumplen 'condicion', y se compara semana a
    semana igual que las demás tarjetas. Replica el campo 'operaciones'
    de reportes.json del sistema original."""
    nombre: str                                  # ej. "IOS"
    hoja_fuente: str                              # nombre de la métrica/hoja de donde se leen las filas
    condicion: list[list[Condicion]] = field(default_factory=list)


@dataclass
class Metrica:
    id: int | None = None
    nombre: str = ""
    categoria: str = ""
    obligatoria: bool = True
    incluir_en_reporte: bool = True
    archivo_patron: str = ""
    archivo_respaldo_patron: str | None = None
    columna_id: str = ""
    limpiar_id: str | None = None
    columnas_separacion: list[str] = field(default_factory=list)
    criterios_incumplimiento: list[list[Condicion]] = field(default_factory=list)
    criterios_limpieza: list[list[Condicion]] = field(default_factory=list)
    enriquecimientos: list[Enriquecimiento] = field(default_factory=list)
    cumplimiento: ConfigCumplimiento = field(default_factory=ConfigCumplimiento)
    funcion_especial: str | None = None
    # Trazabilidad: dónde y cómo descargar el archivo semanal de esta métrica.
    instrucciones_descarga: str = ""
    imagen_instructivo: str | None = None   # ruta relativa a views/static, ej. "uploads/metricas/xxx.png"
    # Presentación PPT: bajo qué barra de sección va (ej. "Agentes - Workstations",
    # "Herramientas - Workstations", "Usuarios", "Antimalware - Dispositivos Moviles").
    # Vacío = la métrica no aparece en el PPT.
    seccion_ppt: str = ""
    # Etiqueta vertical compartida con otras métricas (ej. "MFA" agrupa
    # "Windows hello" + "MFA"). None = tarjeta independiente, sin agrupar.
    grupo_visual_ppt: str | None = None
    # Título que se muestra en la tarjeta del PPT, si es distinto al nombre
    # de la métrica (ej. nombre="MFA" pero en el PPT dice "Registration:").
    titulo_ppt: str | None = None
    # Si True, esta métrica se dibuja como "caja destacada" (formato ancho,
    # antes de la barra de sección) en vez de tarjeta normal en la grilla.
    destacado_ppt: bool = False
    # Subconteos adicionales que se dibujan como filas de comparación
    # simples encima de la tarjeta de esta métrica (ej. IOS/Android).
    operaciones_ppt: list[OperacionPPT] = field(default_factory=list)
    # Orden explícito dentro de su sección/grupo en el PPT (menor = primero).
    # Independiente del orden en que quedó guardada en metricas.json.
    orden_ppt: int = 0
    # Filtro adicional que solo aplica para ciertas entidades (ej. "solo
    # tomar hostname que empiece con IOC, pero solo para BSNC"). Se
    # intersecta (AND) con los criterios normales, únicamente para las
    # entidades presentes como llave en este diccionario. Afecta tanto
    # la hoja del reporte como el cálculo de cumplimiento.
    filtro_entidad: dict[str, list[list[Condicion]]] = field(default_factory=dict)


def _grupos_desde_dict(data: list) -> list[list[Condicion]]:
    return [[Condicion(**c) for c in grupo] for grupo in (data or [])]


def _grupos_a_dict(grupos: list[list[Condicion]]) -> list:
    return [[asdict(c) for c in grupo] for grupo in (grupos or [])]


def _operaciones_desde_dict(data: list) -> list[OperacionPPT]:
    resultado = []
    for op in (data or []):
        resultado.append(OperacionPPT(
            nombre=op.get("nombre", ""),
            hoja_fuente=op.get("hoja_fuente", ""),
            condicion=_grupos_desde_dict(op.get("condicion")),
        ))
    return resultado


def _operaciones_a_dict(operaciones: list[OperacionPPT]) -> list:
    return [{"nombre": op.nombre, "hoja_fuente": op.hoja_fuente,
            "condicion": _grupos_a_dict(op.condicion)} for op in operaciones]


def metrica_desde_dict(d: dict) -> Metrica:
    cump_d = d.get("cumplimiento") or {}
    cumplimiento = ConfigCumplimiento(
        aplica=cump_d.get("aplica", False),
        operador=cump_d.get("operador", ">"),
        umbral=cump_d.get("umbral", 0.97),
        criterio_favor=_grupos_desde_dict(cump_d.get("criterio_favor")),
        criterio_total=_grupos_desde_dict(cump_d.get("criterio_total")),
        criterio_total_fijo=cump_d.get("criterio_total_fijo"),
        excluir=_grupos_desde_dict(cump_d.get("excluir")),
    )
    enriquecimientos = [Enriquecimiento(**e) for e in d.get("enriquecimientos", [])]
    return Metrica(
        id=d.get("id"),
        nombre=d.get("nombre", ""),
        categoria=d.get("categoria", ""),
        obligatoria=d.get("obligatoria", True),
        incluir_en_reporte=d.get("incluir_en_reporte", True),
        archivo_patron=d.get("archivo_patron", ""),
        archivo_respaldo_patron=d.get("archivo_respaldo_patron"),
        columna_id=d.get("columna_id", ""),
        limpiar_id=d.get("limpiar_id"),
        columnas_separacion=list(d.get("columnas_separacion", [])),
        criterios_incumplimiento=_grupos_desde_dict(d.get("criterios_incumplimiento")),
        criterios_limpieza=_grupos_desde_dict(d.get("criterios_limpieza")),
        enriquecimientos=enriquecimientos,
        cumplimiento=cumplimiento,
        funcion_especial=d.get("funcion_especial"),
        instrucciones_descarga=d.get("instrucciones_descarga", ""),
        imagen_instructivo=d.get("imagen_instructivo"),
        seccion_ppt=d.get("seccion_ppt", ""),
        grupo_visual_ppt=d.get("grupo_visual_ppt"),
        titulo_ppt=d.get("titulo_ppt"),
        destacado_ppt=d.get("destacado_ppt", False),
        operaciones_ppt=_operaciones_desde_dict(d.get("operaciones_ppt")),
        orden_ppt=d.get("orden_ppt", 0),
        filtro_entidad={k: _grupos_desde_dict(v) for k, v in (d.get("filtro_entidad") or {}).items()},
    )


def metrica_a_dict(m: Metrica) -> dict:
    return {
        "id": m.id,
        "nombre": m.nombre,
        "categoria": m.categoria,
        "obligatoria": m.obligatoria,
        "incluir_en_reporte": m.incluir_en_reporte,
        "archivo_patron": m.archivo_patron,
        "archivo_respaldo_patron": m.archivo_respaldo_patron,
        "columna_id": m.columna_id,
        "limpiar_id": m.limpiar_id,
        "columnas_separacion": m.columnas_separacion,
        "criterios_incumplimiento": _grupos_a_dict(m.criterios_incumplimiento),
        "criterios_limpieza": _grupos_a_dict(m.criterios_limpieza),
        "enriquecimientos": [asdict(e) for e in m.enriquecimientos],
        "cumplimiento": {
            "aplica": m.cumplimiento.aplica,
            "operador": m.cumplimiento.operador,
            "umbral": m.cumplimiento.umbral,
            "criterio_favor": _grupos_a_dict(m.cumplimiento.criterio_favor),
            "criterio_total": _grupos_a_dict(m.cumplimiento.criterio_total),
            "criterio_total_fijo": m.cumplimiento.criterio_total_fijo,
            "excluir": _grupos_a_dict(m.cumplimiento.excluir),
        },
        "funcion_especial": m.funcion_especial,
        "instrucciones_descarga": m.instrucciones_descarga,
        "imagen_instructivo": m.imagen_instructivo,
        "seccion_ppt": m.seccion_ppt,
        "grupo_visual_ppt": m.grupo_visual_ppt,
        "titulo_ppt": m.titulo_ppt,
        "destacado_ppt": m.destacado_ppt,
        "operaciones_ppt": _operaciones_a_dict(m.operaciones_ppt),
        "orden_ppt": m.orden_ppt,
        "filtro_entidad": {k: _grupos_a_dict(v) for k, v in m.filtro_entidad.items()},
    }


class MetricaRepository(JsonRepository):
    def __init__(self, ruta: Path = None):
        super().__init__(
            ruta_archivo=ruta or (DATA_DIR / "metricas.json"),
            factory=metrica_desde_dict,
            to_dict=metrica_a_dict,
        )

    def obligatorias(self) -> list[Metrica]:
        return [m for m in self.listar() if m.obligatoria]

    def obtener_por_nombre(self, nombre: str):
        for m in self.listar():
            if m.nombre.strip().lower() == nombre.strip().lower():
                return m
        return None

    def incluidas_en_reporte(self) -> list[Metrica]:
        return [m for m in self.listar() if m.incluir_en_reporte]