"""Alias de compatibilidad con la plantilla PPT ORIGINAL (Batxcel6.0),
que usa nombres cortos ('dlp', 'qualys', 'mtd'...) en vez de los nombres
completos de las métricas actuales. Reemplaza el antiguo
MAPEO_RESUMEN_CUMPLIMIENTO. Si algún día se rediseña la plantilla con
los nombres completos, este archivo deja de ser necesario (pero no
estorba dejarlo).
"""

# <<alias>> (comparación semanal, sin sufijo) -> nombre real de la
# métrica que SÍ tiene hoja en el reporte.
ALIAS_HOJA = {
    "dlp": "DLP Netskope",
    "netskope": "Netskope Workstations",
    "netskope_virtuales": "Netskope PC virtuales",
    "qualys": "Qualys no cmdb",
    "harmony": "Harmony Instalado",
    "mtd": "MTD Sincronizado",
    "mtd_client_version": "MTD Version",
    "moviles": "Moviles Compliant",
}

# <<alias_cumplimiento>>, <<alias_umbral>>, <<alias_status>>, etc ->
# nombre real de la métrica de cumplimiento correspondiente.
ALIAS_CUMPLIMIENTO = {
    "dlp": "DLP Netskope",
    "netskope": "Netskope Workstations",
    "qualys": "Qualys cmdb",
    "harmony": "Harmony Instalado",
    "mtd": "MTD Sincronizado",
    "mtd_client_version": "MTD Version",
    "moviles": "Moviles Compliant",
    "moviles_update": "Moviles Update",
}

# <<alias(operacion)>> -> nombre real de la hoja de donde se leen las
# filas para calcular esa operación.
ALIAS_OPERACION_HOJA = {
    "qualys": "Qualys no cmdb",
    "moviles": "Moviles Compliant",
    "moviles_update": "Moviles Compliant",
}