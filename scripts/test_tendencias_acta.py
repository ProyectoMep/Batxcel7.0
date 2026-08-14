"""Prueba del motor de tendencias del acta con datos reales del
histórico. No genera ningún .docx todavía, solo imprime en consola.

Uso: python scripts/test_tendencias_acta.py 2026-08-12 2026-08-11 BSNC
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.acta.tendencias import calcular_tendencias


def main():
    if len(sys.argv) < 3:
        print("❌ Uso: python scripts/test_tendencias_acta.py <fecha_actual> <fecha_anterior> [entidad]")
        return
    fecha_actual, fecha_anterior = sys.argv[1], sys.argv[2]
    entidad = sys.argv[3] if len(sys.argv) > 3 else "BSNC"

    filas = calcular_tendencias(entidad, fecha_actual, fecha_anterior)
    if not filas:
        print("⚠️  No se calculó ninguna fila (revisa que existan las filas_acta y el histórico)")
        return

    print(f"{'Métrica':<28} {'Actual':>7} {'Anterior':>9}  {'Tendencia':<14} Acción")
    print("-" * 100)
    for f in filas:
        print(f"{f['metrica_acta']:<28} {str(f['actual']):>7} {str(f['anterior']):>9}  "
              f"{f['tendencia']:<14} {f['accion']}")


if __name__ == "__main__":
    main()