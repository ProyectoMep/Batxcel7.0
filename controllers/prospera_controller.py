"""Controlador de Usuarios PROSPERA. Prospera siempre trabaja sobre
BSNC (igual que el sistema original) — cruza el Resumen Cyber BSNC de
una fecha con el archivo Cloud_Authentication que subes."""
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file, abort

from config.settings import OUTPUT_DIR, DATA_DIR
from services.ppt.generador_ppt import fechas_disponibles
from services.prospera.generador_prospera import generar_prospera, listar_prospera

prospera_bp = Blueprint("prospera", __name__, url_prefix="/api/prospera")


@prospera_bp.route("/fechas")
def api_fechas():
    return jsonify(fechas_disponibles("BSNC"))


@prospera_bp.route("/historico")
def api_historico():
    return jsonify(listar_prospera())


@prospera_bp.route("/generar", methods=["POST"])
def api_generar():
    fecha = (request.form.get("fecha_resumen") or "").strip()
    nombre = (request.form.get("nombre") or "").strip()
    archivo = request.files.get("archivo")

    import re
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        return jsonify({"ok": False, "error": "Selecciona la fecha del resumen"}), 400
    if archivo is None or not archivo.filename.lower().endswith(".xlsx"):
        return jsonify({"ok": False,
                        "error": "Debes cargar el archivo Cloud_Authentication (.xlsx)"}), 400

    tmp_dir = DATA_DIR / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ruta_tmp = tmp_dir / "cloud_prospera.xlsx"
    archivo.save(ruta_tmp)

    try:
        resultado = generar_prospera(fecha_resumen=fecha, ruta_cloud=ruta_tmp,
                                     nombre=nombre or None)
    finally:
        ruta_tmp.unlink(missing_ok=True)

    return jsonify(resultado), (200 if resultado["ok"] else 400)


def _ruta_segura(ruta_relativa: str) -> Path | None:
    ruta = (OUTPUT_DIR / ruta_relativa).resolve()
    if not str(ruta).startswith(str(OUTPUT_DIR.resolve())) or not ruta.is_file():
        return None
    return ruta


@prospera_bp.route("/descargar/<fecha>/<path:ruta_relativa>")
def api_descargar(fecha, ruta_relativa):
    ruta = _ruta_segura(f"{fecha}/{ruta_relativa}")
    if ruta is None:
        abort(404)
    return send_file(ruta, as_attachment=(request.args.get("dl") == "1"))