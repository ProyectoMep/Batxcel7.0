"""Diagnóstico puntual: llama EXACTAMENTE a las mismas funciones que usa
el generador de PPT (leer_hojas_excel + comparar_excel), para ver qué
cuenta de verdad para la hoja 'Qualys no cmdb', antes de que llegue a
las banderas.

Uso: python scripts/diagnostico_comparativo_ppt.py 2026-08-12 BSNC
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import OUTPUT_DIR
from models.entidad import EntidadRepository
from services.ppt.plantilla_utils import leer_hojas_excel, comparar_excel
from services.ppt.datos_ppt import buscar_archivo_anterior
from services.ppt.banderas import normalizar_clave


def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    entidad_nombre = sys.argv[2] if len(sys.argv) > 2 else "BSNC"
    if fecha is None:
        print("❌ Uso: python scripts/diagnostico_comparativo_ppt.py <fecha> <entidad>")
        return

    repo = EntidadRepository()
    entidad = repo.obtener_por_nombre(entidad_nombre)
    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre

    ruta_actual = OUTPUT_DIR / fecha / f"{nombre_archivo}.xlsx"
    ruta_anterior = buscar_archivo_anterior(nombre_archivo, fecha)

    print(f"📄 Ruta ACTUAL que se está leyendo:   {ruta_actual}")
    print(f"   ¿Existe? {ruta_actual.exists()}")
    print(f"📄 Ruta ANTERIOR que se está leyendo: {ruta_anterior}")
    print(f"   ¿Existe? {ruta_anterior.exists() if ruta_anterior else 'N/A (no se encontró ninguna)'}")

    hojas_actual = leer_hojas_excel(str(ruta_actual))
    hojas_anterior = leer_hojas_excel(str(ruta_anterior)) if ruta_anterior else {}

    print(f"\n📋 Todas las hojas leídas del archivo ACTUAL:")
    for hoja, n in hojas_actual.items():
        marca = "  👉" if normalizar_clave(hoja) == "qualys_no_cmdb" else "   "
        print(f"{marca} '{hoja}' -> {n} filas")

    print(f"\n📋 Todas las hojas leídas del archivo ANTERIOR:")
    for hoja, n in hojas_anterior.items():
        marca = "  👉" if normalizar_clave(hoja) == "qualys_no_cmdb" else "   "
        print(f"{marca} '{hoja}' -> {n} filas")

    comparativo = comparar_excel(hojas_actual, hojas_anterior)
    print(f"\n🔍 Resultado de comparar_excel para 'Qualys no cmdb':")
    if "Qualys no cmdb" in comparativo:
        print(f"   {comparativo['Qualys no cmdb']}")
    else:
        print("   ❌ 'Qualys no cmdb' NO está como llave en el diccionario comparativo")
        print(f"   Llaves disponibles: {list(comparativo.keys())}")


if __name__ == "__main__":
    main()