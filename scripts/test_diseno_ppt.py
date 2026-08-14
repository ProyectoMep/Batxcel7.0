"""Prueba visual del diseño, con datos inventados (sin conectar a
métricas reales todavía). Genera un .pptx de muestra para que revises
que el layout se ve bien antes de conectar los datos reales.

Uso: python scripts/test_diseno_ppt.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pptx.util import Inches
from services.ppt.diseno_ppt import (crear_presentacion, agregar_portada,
                                     agregar_slide_nomenclatura,
                                     agregar_barra_seccion, agregar_encabezado_slide,
                                     dibujar_tarjeta, dibujar_grupo_vertical,
                                     agregar_cierre, formatear_comparacion,
                                     nueva_slide_en_blanco)

DATO_EJEMPLO_1 = {
    "comparacion_texto": formatear_comparacion(0, 0)[0],
    "comparacion_color": formatear_comparacion(0, 0)[1],
    "umbral": 0.97, "numerador": 764, "denominador": 764,
    "resultado_pct": "100.0%", "estado": "Cumple",
}
DATO_EJEMPLO_2 = {
    "comparacion_texto": formatear_comparacion(31, 20)[0],
    "comparacion_color": formatear_comparacion(31, 20)[1],
    "umbral": 0.97, "numerador": 709, "denominador": 740,
    "resultado_pct": "95.8%", "estado": "No Cumple",
}

prs = crear_presentacion()

# 1) Portada
agregar_portada(prs, "BSNC", "12/08/2026",
                "Actualización semanal de los agentes y herramientas sin reportar "
                "o pendientes por configurar en las Workstations y Móviles de Banco.")

# 2) Nomenclatura (estática)
agregar_slide_nomenclatura(prs)

# 3) Sección de ejemplo con tarjetas simples + un grupo vertical
slide = nueva_slide_en_blanco(prs)
agregar_encabezado_slide(slide, "Resumen Cyber BSNC", "12/08/2026")
y = agregar_barra_seccion(slide, "Agentes - Workstations", y=Inches(0.6))
dibujar_tarjeta(slide, Inches(0.4), y, Inches(6), Inches(1.1), "CrowdStrike", DATO_EJEMPLO_1)
dibujar_tarjeta(slide, Inches(6.7), y, Inches(6), Inches(1.1), "DLP Netskope", DATO_EJEMPLO_1)
y += Inches(1.3)
dibujar_grupo_vertical(slide, Inches(0.4), y, Inches(6), Inches(1.6), "MFA", [
    {"titulo": "Windows Hello:", "dato": DATO_EJEMPLO_2},
    {"titulo": "Registration:", "dato": DATO_EJEMPLO_1},
])

# 4) Cierre
agregar_cierre(prs)

prs.save("output_test_diseno.pptx")
print("✅ Generado: output_test_diseno.pptx — ábrelo para revisar el diseño")
print(f"   Total de diapositivas: {len(prs.slides)}")