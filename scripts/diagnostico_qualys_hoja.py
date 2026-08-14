"""Diagnóstico puntual: revisa cuántas filas tiene la hoja 'Qualys no
cmdb' dentro del Excel de reporte ya generado, para saber si el bug
está en la generación del reporte o en la lectura que hace el PPT.

Uso: python scripts/diagnostico_qualys_hoja.py 2026-08-12 BSNC
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import OUTPUT_DIR
from models.entidad import EntidadRepository


def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    entidad_nombre = sys.argv[2] if len(sys.argv) > 2 else "BSNC"
    if fecha is None:
        print("❌ Uso: python scripts/diagnostico_qualys_hoja.py <fecha> <entidad>")
        return

    repo = EntidadRepository()
    entidad = repo.obtener_por_nombre(entidad_nombre)
    if entidad is None:
        print(f"❌ No existe la entidad '{entidad_nombre}'")
        return

    nombre_archivo = entidad.nombre_archivo_salida or entidad.nombre
    ruta = OUTPUT_DIR / fecha / f"{nombre_archivo}.xlsx"
    if not ruta.exists():
        print(f"❌ No existe {ruta}")
        return

    print(f"📄 Archivo: {ruta}\n")
    xl = pd.ExcelFile(ruta)
    print("Hojas encontradas en el archivo:")
    for hoja in xl.sheet_names:
        print(f"   - '{hoja}'")

    objetivo = "qualys no cmdb"
    print(f"\nBuscando hoja que normalice a '{objetivo.replace(' ', '_')}'...")
    encontrada = None
    for hoja in xl.sheet_names:
        if hoja.strip().lower() == objetivo:
            encontrada = hoja
            break

    if encontrada is None:
        print("❌ No se encontró ninguna hoja llamada exactamente 'Qualys no cmdb'")
        return

    df = xl.parse(encontrada)
    print(f"\n✅ Hoja encontrada: '{encontrada}'")
    print(f"   Filas: {len(df)}")
    if len(df) > 0:
        print(f"   Columnas: {list(df.columns)}")
        print(df.head(10).to_string())


if __name__ == "__main__":
    main()