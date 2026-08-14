"""Controlador de Reportes: expone el estado de archivos de entrada,
dispara la generación en segundo plano, y permite navegar/descargar el
histórico de output/. Reemplaza la Sección 1 de run.py del sistema
original."""
import threading
from pathlib import Path
import pandas as pd
from flask import Blueprint, jsonify, send_file, abort, request

from config.settings import OUTPUT_DIR
from models.metrica import MetricaRepository
from services.resolver_archivo import resolver_archivo_de_metrica
from services.generador_reporte import generar_reporte

reporte_bp = Blueprint("reporte", __name__, url_prefix="/api/reporte")

_estado_proceso = {"corriendo": False, "resultado": None}


def _worker():
    resultado = generar_reporte()
    _estado_proceso["resultado"] = resultado
    _estado_proceso["corriendo"] = False


def _ruta_segura(fecha: str, nombre: str) -> Path | None:
    ruta = (OUTPUT_DIR / fecha / nombre).resolve()
    if not str(ruta).startswith(str(OUTPUT_DIR.resolve())) or not ruta.is_file():
        return None
    return ruta


@reporte_bp.route("/estado-input")
def estado_input():
    """Detalle por métrica obligatoria: encontrada o no, con sus
    instrucciones e imagen de referencia para el modal del ojo."""
    repo = MetricaRepository()
    metricas = [m for m in repo.listar() if m.obligatoria]

    detalle = []
    faltantes = []
    for m in metricas:
        ruta, es_respaldo = resolver_archivo_de_metrica(m)
        encontrado = ruta is not None
        if not encontrado:
            faltantes.append(m.nombre)
        detalle.append({
            "nombre": m.nombre,
            "encontrado": encontrado,
            "es_respaldo": es_respaldo,
            "archivo": ruta.name if ruta else None,
            "archivo_patron": m.archivo_patron,
            "instrucciones_descarga": m.instrucciones_descarga,
            "imagen_instructivo": m.imagen_instructivo,
        })

    return jsonify({"metricas": detalle, "faltantes": faltantes})


@reporte_bp.route("/generar", methods=["POST"])
def generar():
    if _estado_proceso["corriendo"]:
        return jsonify({"ok": False, "error": "Ya hay un proceso en ejecución"}), 409

    repo = MetricaRepository()
    metricas = [m for m in repo.listar() if m.obligatoria]
    faltantes = [m.nombre for m in metricas if resolver_archivo_de_metrica(m)[0] is None]
    if faltantes:
        return jsonify({"ok": False,
                        "error": "Faltan archivos obligatorios: " + ", ".join(faltantes)}), 400

    _estado_proceso["corriendo"] = True
    _estado_proceso["resultado"] = None
    threading.Thread(target=_worker, daemon=True).start()
    return jsonify({"ok": True})


@reporte_bp.route("/estado-proceso")
def estado_proceso():
    return jsonify(_estado_proceso)


@reporte_bp.route("/arbol-output")
def arbol_output():
    arbol = []
    if not OUTPUT_DIR.exists():
        return jsonify(arbol)
    for carpeta in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not carpeta.is_dir():
            continue
        archivos = sorted(f.name for f in carpeta.glob("*.xlsx"))
        if archivos:
            arbol.append({"fecha": carpeta.name, "archivos": archivos})
    return jsonify(arbol)


@reporte_bp.route("/descargar/<fecha>/<path:nombre>")
def descargar(fecha, nombre):
    ruta = _ruta_segura(fecha, nombre)
    if ruta is None:
        abort(404)
    return send_file(ruta, as_attachment=(request.args.get("dl") == "1"))


@reporte_bp.route("/preview/<fecha>/<path:nombre>")
def preview(fecha, nombre):
    ruta = _ruta_segura(fecha, nombre)
    if ruta is None:
        return jsonify({"ok": False, "error": "Archivo no encontrado"}), 404
    try:
        xl = pd.ExcelFile(ruta)
        hojas = []
        for h in xl.sheet_names:
            df = xl.parse(h, nrows=100).fillna("")
            hojas.append({"nombre": h, "filas": len(df),
                          "html": df.to_html(index=False, border=0)})
        return jsonify({"ok": True, "hojas": hojas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500