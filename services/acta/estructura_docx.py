"""Localiza las tablas conocidas dentro de un acta .docx (info general,
participantes, métricas, observaciones, glosario) por el texto de su
encabezado. Se usa tanto para LEER (extraer_acta.py) como para EDITAR
en el mismo lugar (generador_acta.py) — así el documento final conserva
exactamente el diseño (fuente, márgenes, encabezados) del archivo que
se abrió, en vez de perderlo al construir uno nuevo desde cero.
"""


def tabla_info_general(doc):
    for t in doc.tables:
        if t.rows and t.rows[0].cells[0].text.strip().lower() == "fecha":
            return t
    return None


def tabla_participantes(doc):
    for t in doc.tables:
        if not t.rows:
            continue
        encabezado = [c.text.strip().lower() for c in t.rows[0].cells]
        if encabezado and "nombre" in encabezado[0]:
            return t
    return None


def tabla_metricas(doc):
    for t in doc.tables:
        if not t.rows or len(t.columns) != 4:
            continue
        encabezado = [c.text.strip().lower() for c in t.rows[0].cells]
        if encabezado[0].startswith("métrica") and len(encabezado) > 1 and "tendencia" in encabezado[1]:
            return t
    return None


def tabla_observaciones(doc):
    candidatas = [t for t in doc.tables if len(t.columns) == 1 and t.rows]
    for t in candidatas:
        primer_texto = t.rows[0].cells[0].text.strip()
        if primer_texto.startswith("•") or primer_texto.startswith("-"):
            return t
    return candidatas[0] if candidatas else None


def tabla_glosario(doc):
    for t in doc.tables:
        if not t.rows or len(t.columns) != 2:
            continue
        encabezado = [c.text.strip().lower() for c in t.rows[0].cells]
        if encabezado[0].startswith("métrica") and len(encabezado) > 1 and "descripción" in encabezado[1]:
            return t
    return None


def limpiar_filas_datos(tabla):
    """Elimina todas las filas menos el encabezado (fila 0)."""
    for row in list(tabla.rows[1:]):
        tabla._tbl.remove(row._tr)