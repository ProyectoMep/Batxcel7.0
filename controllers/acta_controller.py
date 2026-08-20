"""Controlador de Actas: CRUD de asistentes y observaciones, selector de
'presentación de origen' (igual que el sistema original, en vez de
elegir 2 fechas sueltas), generar acta, histórico y descarga."""
import json
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file, abort

from config.settings import OUTPUT_DIR
from models.asistente import AsistenteRepository, Asistente
from models.observacion import ObservacionRepository, Observacion
from services.ppt.generador_ppt import listar_presentaciones
from services.acta.generador_acta import generar_acta, listar_actas
from services.acta.extraer_acta import importar_desde_acta

acta_bp = Blueprint("acta", __name__, url_prefix="/api/acta")


# ── Asistentes ──

@acta_bp.route("/asistentes/<entidad>", methods=["GET"])
def listar_asistentes(entidad):
    repo = AsistenteRepository(entidad)
    return jsonify([{"id": a.id, "nombre": a.nombre, "cargo": a.cargo, "estado": a.estado}
                    for a in repo.listar()])


@acta_bp.route("/asistentes/<entidad>", methods=["POST"])
def crear_asistente(entidad):
    d = request.get_json(force=True)
    nombre = (d.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400
    repo = AsistenteRepository(entidad)
    creado = repo.crear(Asistente(nombre=nombre, cargo=(d.get("cargo") or "").strip(),
                                  estado=(d.get("estado") or "Asistió").strip()))
    return jsonify({"ok": True, "asistente": {"id": creado.id, "nombre": creado.nombre,
                                              "cargo": creado.cargo, "estado": creado.estado}}), 201


@acta_bp.route("/asistentes/<entidad>/<int:id_>", methods=["PUT"])
def editar_asistente(entidad, id_):
    d = request.get_json(force=True)
    nombre = (d.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"ok": False, "error": "El nombre es obligatorio"}), 400
    repo = AsistenteRepository(entidad)
    actualizado = repo.actualizar(id_, Asistente(
        nombre=nombre, cargo=(d.get("cargo") or "").strip(),
        estado=(d.get("estado") or "Asistió").strip()))
    if actualizado is None:
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    return jsonify({"ok": True, "asistente": {"id": actualizado.id, "nombre": actualizado.nombre,
                                              "cargo": actualizado.cargo, "estado": actualizado.estado}})


@acta_bp.route("/asistentes/<entidad>/<int:id_>", methods=["DELETE"])
def eliminar_asistente(entidad, id_):
    repo = AsistenteRepository(entidad)
    ok = repo.eliminar(id_)
    if not ok:
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    return jsonify({"ok": True})


# ── Observaciones ──

@acta_bp.route("/observaciones/<entidad>", methods=["GET"])
def listar_observaciones(entidad):
    repo = ObservacionRepository(entidad)
    return jsonify([{"id": o.id, "texto": o.texto} for o in repo.listar()])


@acta_bp.route("/observaciones/<entidad>", methods=["POST"])
def crear_observacion(entidad):
    d = request.get_json(force=True)
    texto = (d.get("texto") or "").strip()
    if not texto:
        return jsonify({"ok": False, "error": "El texto es obligatorio"}), 400
    repo = ObservacionRepository(entidad)
    creada = repo.crear(Observacion(texto=texto))
    return jsonify({"ok": True, "observacion": {"id": creada.id, "texto": creada.texto}}), 201


@acta_bp.route("/observaciones/<entidad>/<int:id_>", methods=["DELETE"])
def eliminar_observacion(entidad, id_):
    repo = ObservacionRepository(entidad)
    ok = repo.eliminar(id_)
    if not ok:
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    return jsonify({"ok": True})


# ── Presentaciones de origen (reemplaza elegir 2 fechas sueltas) ──

@acta_bp.route("/presentaciones/<entidad>")
def api_presentaciones(entidad):
    """Lista las presentaciones PPT generadas para esta entidad, con su
    fecha_actual/fecha_anterior ya resueltas (leídas del .json que se
    guarda junto al .pptx), para que el acta se genere con las mismas
    fechas que se usaron en la presentación de origen."""
    historico = listar_presentaciones()
    items = historico.get(entidad.upper(), [])
    resultado = []
    for it in items:
        ruta_pptx = OUTPUT_DIR / it["fecha"] / it["pptx"]
        ruta_json = ruta_pptx.with_suffix(".json")
        meta = {}
        if ruta_json.exists():
            try:
                meta = json.loads(ruta_json.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        resultado.append({
            "fecha": it["fecha"], "nombre": it["nombre"],
            "fecha_actual": meta.get("fecha_actual", it["fecha"]),
            "fecha_anterior": meta.get("fecha_anterior", ""),
        })
    return jsonify(resultado)


# ── Importar / generar / histórico ──

@acta_bp.route("/importar/<entidad>", methods=["POST"])
def api_importar(entidad):
    """Importa asistentes y observaciones desde la última acta .docx
    generada (o colocada manualmente) en output/*/actas/<entidad>/.
    REEMPLAZA lo que hubiera en la interfaz (borra primero), para que
    nunca queden duplicados."""
    resultado = importar_desde_acta(entidad.upper())
    if not resultado["ok"]:
        return jsonify(resultado), 404

    asis_repo = AsistenteRepository(entidad)
    obs_repo = ObservacionRepository(entidad)

    for a in asis_repo.listar():
        asis_repo.eliminar(a.id)
    for o in obs_repo.listar():
        obs_repo.eliminar(o.id)

    for a in resultado["asistentes"]:
        asis_repo.crear(Asistente(nombre=a["nombre"], cargo=a.get("cargo", ""),
                                  estado=a.get("estado") or "Asistió"))
    for texto in resultado["observaciones"]:
        obs_repo.crear(Observacion(texto=texto))

    return jsonify({"ok": True, "archivo": resultado["archivo"],
                    "asistentes_importados": len(resultado["asistentes"]),
                    "observaciones_importadas": len(resultado["observaciones"])})


@acta_bp.route("/generar", methods=["POST"])
def api_generar():
    d = request.get_json(force=True)
    entidad = (d.get("entidad") or "").upper()
    fecha_actual = d.get("fecha_actual") or ""
    fecha_anterior = d.get("fecha_anterior") or ""
    numero = d.get("numero") or ""
    fecha_reunion = d.get("fecha_reunion") or ""
    nombre = d.get("nombre") or None

    if not all([entidad, fecha_actual, fecha_anterior, numero, fecha_reunion]):
        return jsonify({"ok": False, "error": "Faltan campos obligatorios "
                                              "(entidad, presentación de origen, número, fecha de reunión)"}), 400

    resultado = generar_acta(entidad, fecha_actual, fecha_anterior, numero, fecha_reunion, nombre)
    return jsonify(resultado), (200 if resultado["ok"] else 400)


@acta_bp.route("/historico")
def api_historico():
    return jsonify(listar_actas())


def _ruta_segura(ruta_relativa: str) -> Path | None:
    ruta = (OUTPUT_DIR / ruta_relativa).resolve()
    if not str(ruta).startswith(str(OUTPUT_DIR.resolve())) or not ruta.is_file():
        return None
    return ruta


@acta_bp.route("/descargar/<fecha>/<path:ruta_relativa>")
def api_descargar(fecha, ruta_relativa):
    ruta = _ruta_segura(f"{fecha}/{ruta_relativa}")
    if ruta is None:
        abort(404)
    return send_file(ruta, as_attachment=(request.args.get("dl") == "1"))