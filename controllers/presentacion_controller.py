"""Controlador de Presentación PPT: expone fechas disponibles por
entidad, el historial de presentaciones generadas, el botón de generar,
y la descarga de archivos (pptx/pdf)."""
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file, abort

from config.settings import OUTPUT_DIR
from services.ppt.generador_ppt import fechas_disponibles, listar_presentaciones, generar_presentacion

presentacion_bp = Blueprint("presentacion", __name__, url_prefix="/api/presentacion")


@presentacion_bp.route("/fechas/<entidad>")
def api_fechas(entidad):
    return jsonify(fechas_disponibles(entidad.upper()))


@presentacion_bp.route("/historico")
def api_historico():
    return jsonify(listar_presentaciones())


@presentacion_bp.route("/generar", methods=["POST"])
def api_generar():
    d = request.get_json(force=True)
    entidad = (d.get("entidad") or "").upper()
    fecha_actual = d.get("fecha_actual") or ""
    fecha_anterior = d.get("fecha_anterior") or None
    nombre = d.get("nombre") or None

    if not entidad or not fecha_actual:
        return jsonify({"ok": False, "error": "Debes indicar entidad y fecha actual"}), 400

    resultado = generar_presentacion(entidad, fecha_actual, fecha_anterior, nombre)
    return jsonify(resultado), (200 if resultado["ok"] else 400)


def _ruta_segura(ruta_relativa: str) -> Path | None:
    ruta = (OUTPUT_DIR / ruta_relativa).resolve()
    if not str(ruta).startswith(str(OUTPUT_DIR.resolve())) or not ruta.is_file():
        return None
    return ruta


@presentacion_bp.route("/descargar/<fecha>/<path:ruta_relativa>")
def api_descargar(fecha, ruta_relativa):
    ruta = _ruta_segura(f"{fecha}/{ruta_relativa}")
    if ruta is None:
        abort(404)
    return send_file(ruta, as_attachment=(request.args.get("dl") == "1"))