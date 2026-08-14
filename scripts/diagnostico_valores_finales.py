"""Diagnóstico puntual: llama a la función que arma el diccionario final
de banderas (_construir_valores dentro de ppt_core.py), usando datos
reales, e imprime exactamente lo que contiene para 'qualys' y
'qualys_no_cmdb' — para ver qué llega de verdad al reemplazo de texto.

Uso: python scripts/diagnostico_valores_finales.py 2026-08-12 BSNC
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from config.settings import OUTPUT_DIR
from models.metrica import MetricaRepository
from models.entidad import EntidadRepository
from services.ppt.plantilla_utils import leer_hojas_excel, comparar_excel
from services.ppt.datos_ppt import buscar_archivo_anterior, cargar_cumplimiento
from services.ppt.ppt_core import _construir_valores


def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    entidad_nombre = sys.argv[2] if len(sys.argv) > 2 else "BSNC"
    if fecha is None:
        print("❌ Uso: python scripts/diagnostico_valores_finales.py <fecha> <entidad>")
        return

    repo_entidad = EntidadRepository()
    entidad = repo_entidad.obtener_por_nombre(entidad_nombre)
    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre

    ruta_actual = OUTPUT_DIR / fecha / f"{nombre_archivo}.xlsx"
    ruta_anterior = buscar_archivo_anterior(nombre_archivo, fecha)
    ruta_cumplimiento = OUTPUT_DIR / fecha / f"resumen_cumplimiento_{entidad.nombre.lower()}.xlsx"

    hojas_actual = leer_hojas_excel(str(ruta_actual))
    hojas_anterior = leer_hojas_excel(str(ruta_anterior)) if ruta_anterior else {}
    comparativo = comparar_excel(hojas_actual, hojas_anterior)
    cumplimiento_map = cargar_cumplimiento(ruta_cumplimiento)

    metricas = MetricaRepository().listar()
    fecha_texto = datetime.now().strftime("%d/%m/%Y")
    titulo = ruta_actual.stem

    valores = _construir_valores(metricas, comparativo, cumplimiento_map, fecha_texto, titulo)

    print("🔍 Valores relacionados con Qualys en el diccionario final:\n")
    for clave in sorted(valores.keys()):
        if "qualys" in clave.lower():
            print(f"   '{clave}' = {valores[clave]!r}")


if __name__ == "__main__":
    main()