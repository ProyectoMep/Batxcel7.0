"""Controlador de Actas: CRUD de asistentes y observaciones (siempre
editables, no dependen de ningún .docx), fechas disponibles, generar
acta, histórico y descarga."""
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file, abort

from config.settings import OUTPUT_DIR
from models.asistente import AsistenteRepository, Asistente
from models.observacion import ObservacionRepository, Observacion
from services.ppt.generador_ppt import fechas_disponibles
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


# ── Fechas / generación / histórico ──

@acta_bp.route("/fechas/<entidad>")
def api_fechas(entidad):
    return jsonify(fechas_disponibles(entidad.upper()))


@acta_bp.route("/importar/<entidad>", methods=["POST"])
def api_importar(entidad):
    """Importa asistentes y observaciones desde la última acta .docx
    generada (o colocada manualmente) en output/*/actas/<entidad>/, y
    los guarda en los JSON editables. No duplica: si un asistente
    (mismo nombre) o una observación (mismo texto) ya existe, se omite."""
    resultado = importar_desde_acta(entidad.upper())
    if not resultado["ok"]:
        return jsonify(resultado), 404

    asis_repo = AsistenteRepository(entidad)
    obs_repo = ObservacionRepository(entidad)

    nombres_existentes = {a.nombre.strip().lower() for a in asis_repo.listar()}
    textos_existentes = {o.texto.strip().lower() for o in obs_repo.listar()}

    agregados_asistentes = 0
    for a in resultado["asistentes"]:
        if a["nombre"].strip().lower() in nombres_existentes:
            continue
        asis_repo.crear(Asistente(nombre=a["nombre"], cargo=a.get("cargo", ""),
                                  estado=a.get("estado", "Asistió")))
        nombres_existentes.add(a["nombre"].strip().lower())
        agregados_asistentes += 1

    agregados_observaciones = 0
    for texto in resultado["observaciones"]:
        if texto.strip().lower() in textos_existentes:
            continue
        obs_repo.crear(Observacion(texto=texto))
        textos_existentes.add(texto.strip().lower())
        agregados_observaciones += 1

    return jsonify({"ok": True, "archivo": resultado["archivo"],
                    "asistentes_importados": agregados_asistentes,
                    "observaciones_importadas": agregados_observaciones,
                    "asistentes_omitidos": len(resultado["asistentes"]) - agregados_asistentes,
                    "observaciones_omitidas": len(resultado["observaciones"]) - agregados_observaciones})


@acta_bp.route("/generar", methods=["POST"])
def api_generar():
    d = request.get_json(force=True)
    entidad = (d.get("entidad") or "").upper()
    fecha_actual = d.get("fecha_actual") or ""
    fecha_anterior = d.get("fecha_anterior") or ""
    numero = d.get("numero") or ""
    fecha_reunion = d.get("fecha_reunion") or ""
    hora_inicio = d.get("hora_inicio") or ""
    hora_fin = d.get("hora_fin") or ""
    nombre = d.get("nombre") or None

    if not all([entidad, fecha_actual, fecha_anterior, numero, fecha_reunion]):
        return jsonify({"ok": False, "error": "Faltan campos obligatorios "
                                              "(entidad, fecha actual, fecha anterior, número, fecha de reunión)"}), 400

    resultado = generar_acta(entidad, fecha_actual, fecha_anterior, numero, fecha_reunion,
                             hora_inicio, hora_fin, nombre)
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