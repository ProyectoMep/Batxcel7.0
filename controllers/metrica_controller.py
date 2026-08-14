"""Controlador de Métricas: CRUD + análisis de archivo subido + subida
de imagen de referencia + banderas PPT de cada métrica.
No contiene lógica de negocio pesada, delega en repository/services."""
import re
import time
from pathlib import Path
from flask import Blueprint, jsonify, request
from models.metrica import MetricaRepository, metrica_desde_dict, metrica_a_dict
from services.analizador_archivos import analizar_archivo_subido
from services.ppt.banderas import banderas_de_metrica
from config.settings import BASE_DIR

metrica_bp = Blueprint("metrica", __name__, url_prefix="/api/metricas")
_repo = MetricaRepository()

EXTENSIONES_DATOS_VALIDAS = (".xlsx", ".xls", ".csv")
EXTENSIONES_IMAGEN_VALIDAS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
CARPETA_IMAGENES = BASE_DIR / "views" / "static" / "uploads" / "metricas"


@metrica_bp.route("", methods=["GET"])
def listar():
    return jsonify([metrica_a_dict(m) for m in _repo.listar()])


@metrica_bp.route("/<int:id_>", methods=["GET"])
def obtener(id_):
    m = _repo.obtener(id_)
    if m is None:
        return jsonify({"ok": False, "error": "Métrica no encontrada"}), 404
    return jsonify(metrica_a_dict(m))


@metrica_bp.route("", methods=["POST"])
def crear():
    data = request.get_json(force=True)
    error = _validar(data)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    nueva = metrica_desde_dict(data)
    creada = _repo.crear(nueva)
    return jsonify({"ok": True, "metrica": metrica_a_dict(creada)}), 201


@metrica_bp.route("/<int:id_>", methods=["PUT"])
def actualizar(id_):
    data = request.get_json(force=True)
    error = _validar(data)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    actualizada = _repo.actualizar(id_, metrica_desde_dict(data))
    if actualizada is None:
        return jsonify({"ok": False, "error": "Métrica no encontrada"}), 404
    return jsonify({"ok": True, "metrica": metrica_a_dict(actualizada)})


@metrica_bp.route("/<int:id_>", methods=["DELETE"])
def eliminar(id_):
    ok = _repo.eliminar(id_)
    if not ok:
        return jsonify({"ok": False, "error": "Métrica no encontrada"}), 404
    return jsonify({"ok": True})


@metrica_bp.route("/<int:id_>/banderas", methods=["GET"])
def banderas(id_):
    m = _repo.obtener(id_)
    if m is None:
        return jsonify({"ok": False, "error": "Métrica no encontrada"}), 404
    return jsonify({"ok": True, "metrica": m.nombre, "banderas": banderas_de_metrica(m)})


@metrica_bp.route("/analizar-archivo", methods=["POST"])
def analizar_archivo():
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        return jsonify({"ok": False, "error": "No se recibió ningún archivo"}), 400
    ext = Path(archivo.filename).suffix.lower()
    if ext not in EXTENSIONES_DATOS_VALIDAS:
        return jsonify({"ok": False,
                        "error": "Formato no soportado (usa .xlsx, .xls o .csv)"}), 400

    resultado = analizar_archivo_subido(archivo)
    if not resultado["columnas"]:
        return jsonify({"ok": False,
                        "error": "No se pudieron leer columnas de ese archivo"}), 400
    return jsonify({"ok": True, **resultado})


@metrica_bp.route("/subir-imagen", methods=["POST"])
def subir_imagen():
    """Guarda la imagen de referencia de una métrica en
    views/static/uploads/metricas/ y retorna la ruta relativa (servible
    directo por Flask vía /static/...)."""
    archivo = request.files.get("imagen")
    if archivo is None or not archivo.filename:
        return jsonify({"ok": False, "error": "No se recibió ninguna imagen"}), 400

    ext = Path(archivo.filename).suffix.lower()
    if ext not in EXTENSIONES_IMAGEN_VALIDAS:
        return jsonify({"ok": False,
                        "error": "Formato no soportado (usa png, jpg, jpeg, gif o webp)"}), 400

    CARPETA_IMAGENES.mkdir(parents=True, exist_ok=True)

    nombre_seguro = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(archivo.filename).stem)
    nombre_final = f"{nombre_seguro}_{int(time.time())}{ext}"
    archivo.save(CARPETA_IMAGENES / nombre_final)

    ruta_relativa = f"uploads/metricas/{nombre_final}"
    return jsonify({"ok": True, "ruta": ruta_relativa})


def _validar(data: dict) -> str | None:
    if not data.get("nombre", "").strip():
        return "El nombre de la métrica es obligatorio"
    if not data.get("archivo_patron", "").strip():
        return "El patrón de archivo es obligatorio"
    if not data.get("columna_id", "").strip():
        return "La columna ID es obligatoria"
    return None