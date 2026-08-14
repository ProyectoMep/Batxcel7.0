"""Manejo del histórico: mueve el contenido de input/ a procesados/<fecha>/
después de generar el reporte, para no volver a procesar los mismos
archivos la próxima semana. Reemplaza la función equivalente de
src/historico.py del sistema original.
"""
import shutil
from pathlib import Path
from config.settings import INPUT_DIR, PROCESADOS_DIR


def mover_inputs_a_procesados(fecha: str) -> int:
    """Mueve todo el contenido de input/ a procesados/<fecha>/.
    Retorna cuántos archivos se movieron. Si un archivo con el mismo
    nombre ya existe en el destino, lo sobrescribe (evita fallar si el
    reporte se corre más de una vez el mismo día)."""
    destino = PROCESADOS_DIR / fecha
    destino.mkdir(parents=True, exist_ok=True)

    movidos = 0
    for archivo in INPUT_DIR.iterdir():
        if not archivo.is_file():
            continue
        ruta_destino = destino / archivo.name
        if ruta_destino.exists():
            ruta_destino.unlink()
        shutil.move(str(archivo), str(ruta_destino))
        movidos += 1
    return movidos