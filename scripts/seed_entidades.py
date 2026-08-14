"""Script de una sola vez: crea/actualiza en data/entidades.json las
entidades BSNC y SF. Idempotente.

Ejecutar desde la raíz del proyecto: python scripts/seed_entidades.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.entidad import Entidad, EntidadRepository

repo = EntidadRepository()

ENTIDADES = [
    Entidad(
        nombre="BSNC",
        nombre_archivo_salida="Resumen Cyber BSNC",
        identificadores=["BS de Negocios Colombia", "Santander Colombia", "SNC", "SEC", "SBI", "UNC"],
        plantilla_ppt="Plantilla resumen BSNC.pptx",
        tema_acta="Seguimiento de agentes, software de alto riesgo y cobertura de herramientas "
                  "de seguridad (Workstations BSNC)",
        objetivo_acta="Realizar seguimiento y análisis a los planes y fechas de atención del "
                      "software de alto riesgo, agentes y cobertura de herramientas de seguridad "
                      "en las Workstations y móviles BSNC.",
    ),
    Entidad(
        nombre="SF",
        nombre_archivo_salida="Resumen Cyber SF",
        identificadores=["Santander Financing Colombia", "Santander Consumer Finance Colombia",
                          "financing", "N/A", "CO2", "PCR"],
        plantilla_ppt="Plantilla resumen SF.pptx",
        tema_acta="Seguimiento de agentes, software de alto riesgo y cobertura de herramientas "
                  "de seguridad (Workstations SF)",
        objetivo_acta="Realizar seguimiento y análisis a los planes y fechas de atención del "
                      "software de alto riesgo, agentes y cobertura de herramientas de seguridad "
                      "en las Workstations y móviles SF.",
    ),
]


def main():
    for entidad in ENTIDADES:
        existente = repo.obtener_por_nombre(entidad.nombre)
        if existente:
            repo.actualizar(existente.id, entidad)
            print(f"  🔄 Actualizada: {entidad.nombre}")
        else:
            repo.crear(entidad)
            print(f"  ✅ Creada: {entidad.nombre}")
    print(f"\nListo. {len(ENTIDADES)} entidad(es) procesada(s).")


if __name__ == "__main__":
    main()