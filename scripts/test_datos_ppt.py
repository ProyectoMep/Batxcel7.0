"""Prueba de la capa de datos del PPT: no dibuja nada, solo imprime en
consola lo que se leyó y calculó, para verificar que la comparación
semanal y el cumplimiento se arman bien antes de conectar el dibujo.

Uso: python scripts/test_datos_ppt.py <fecha, ej 2026-08-12> <BSNC|SF>
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.entidad import EntidadRepository
from services.ppt.datos_ppt import obtener_datos_para_ppt


def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    entidad_nombre = sys.argv[2] if len(sys.argv) > 2 else "BSNC"

    if fecha is None:
        print("❌ Debes pasar la fecha. Ej: python scripts/test_datos_ppt.py 2026-08-12 BSNC")
        return

    repo = EntidadRepository()
    entidad = repo.obtener_por_nombre(entidad_nombre)
    if entidad is None:
        print(f"❌ No existe la entidad '{entidad_nombre}'")
        return

    datos = obtener_datos_para_ppt(entidad.nombre, entidad.nombre_archivo_salida or entidad.nombre, fecha)

    print(f"📅 Fecha actual: {fecha}")
    print(f"📅 ¿Se encontró reporte anterior para comparar? {datos['fecha_anterior_encontrada']}\n")

    for nombre_seccion, items in datos["secciones"]:
        print(f"{'=' * 60}\n📁 SECCIÓN: {nombre_seccion}\n{'=' * 60}")
        for item in items:
            if item["tipo"] == "simple":
                m, dato = item["metrica"], item["dato"]
                titulo = m.titulo_ppt or m.nombre
                print(f"\n  🔹 {titulo}")
                print(f"     {dato['comparacion_texto']}")
                print(f"     Umbral: {dato['umbral']*100:.0f}%  "
                      f"Num: {dato['numerador']}  Den: {dato['denominador']}  "
                      f"Resultado: {dato['resultado_pct']}  Estado: {dato['estado']}")
            else:
                print(f"\n  📦 GRUPO: {item['etiqueta']}")
                for sub in item["items"]:
                    m, dato = sub["metrica"], sub["dato"]
                    titulo = m.titulo_ppt or m.nombre
                    print(f"     🔸 {titulo}")
                    print(f"        {dato['comparacion_texto']}")
                    print(f"        Umbral: {dato['umbral']*100:.0f}%  "
                          f"Num: {dato['numerador']}  Den: {dato['denominador']}  "
                          f"Resultado: {dato['resultado_pct']}  Estado: {dato['estado']}")


if __name__ == "__main__":
    main()