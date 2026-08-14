"""Controlador de Entidades: CRUD puro (ver/crear/actualizar/eliminar)."""
from flask import Blueprint, jsonify, request
from models.entidad import EntidadRepository, entidad_desde_dict, entidad_a_dict

entidad_bp = Blueprint("entidad", __name__, url_prefix="/api/entidades")
_repo = EntidadRepository()


@entidad_bp.route("", methods=["GET"])
def listar():
    return jsonify([entidad_a_dict(e) for e in _repo.listar()])


@entidad_bp.route("/<int:id_>", methods=["GET"])
def obtener(id_):
    e = _repo.obtener(id_)
    if e is None:
        return jsonify({"ok": False, "error": "Entidad no encontrada"}), 404
    return jsonify(entidad_a_dict(e))


@entidad_bp.route("", methods=["POST"])
def crear():
    data = request.get_json(force=True)
    error = _validar(data)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    creada = _repo.crear(entidad_desde_dict(data))
    return jsonify({"ok": True, "entidad": entidad_a_dict(creada)}), 201


@entidad_bp.route("/<int:id_>", methods=["PUT"])
def actualizar(id_):
    data = request.get_json(force=True)
    error = _validar(data)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    actualizada = _repo.actualizar(id_, entidad_desde_dict(data))
    if actualizada is None:
        return jsonify({"ok": False, "error": "Entidad no encontrada"}), 404
    return jsonify({"ok": True, "entidad": entidad_a_dict(actualizada)})


@entidad_bp.route("/<int:id_>", methods=["DELETE"])
def eliminar(id_):
    ok = _repo.eliminar(id_)
    if not ok:
        return jsonify({"ok": False, "error": "Entidad no encontrada"}), 404
    return jsonify({"ok": True})


def _validar(data: dict) -> str | None:
    if not data.get("nombre", "").strip():
        return "El nombre de la entidad es obligatorio"
    if not data.get("identificadores"):
        return "Debes agregar al menos un identificador"
    return None