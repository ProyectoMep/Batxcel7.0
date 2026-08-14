"""Script de una sola vez: crea/actualiza en data/metricas.json las 20
métricas del sistema original, replicando exactamente la lógica de
config/reportes.json + config/cumplimiento.json + config/enriquecimiento.json
+ config/limpieza.json + config/separacion.json. Es idempotente: si la
métrica ya existe (por nombre), la actualiza en vez de duplicarla.

Los nombres usados aquí son los de cumplimiento.json (la columna
"Métrica" del resumen de cumplimiento), que también se usan como nombre
de hoja del reporte cuando incluir_en_reporte=True.

Ejecutar desde la raíz del proyecto: python scripts/seed_metricas.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.metrica import (Metrica, Condicion, Enriquecimiento,
                            ConfigCumplimiento, OperacionPPT, MetricaRepository)

repo = MetricaRepository()

# Enriquecimientos reutilizados por varias métricas de "Dispositivos Móviles"
CRUCE_SOFTERRA_POR_EMPLEADO = Enriquecimiento(
    archivo_patron="softerra.xlsx",
    columna_base="user principal name",
    columna_cruzar="employeenumber",
    columnas_extraer=["title", "company_softerra", "description"],
    texto_a_quitar_del_base="@ucloud.santandergroup.net",
)

CRUCE_CMDB_POR_DESCRIPCION = Enriquecimiento(
    archivo_patron="cmdb_ci_computer.xlsx",
    columna_base="description",
    columna_cruzar="Assigned to",
    columnas_extraer=["Name"],
)


def cruce_user_legal_name(columna_base_username: str) -> Enriquecimiento:
    return Enriquecimiento(
        archivo_patron="USER.xlsx",
        columna_base=columna_base_username,
        columna_cruzar="CF - ESI - ESP Local Id",
        columnas_extraer=["Legal Name"],
        texto_a_quitar_del_base="@ucloud.santandergroup.net",
    )


METRICAS = [

    Metrica(
        nombre="High Risk Software",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="high risk software*.xlsx",
        archivo_respaldo_patron="high risk software*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[],  # sin criterios -> todas las filas
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador="<", umbral=0.05,
            criterio_favor=[],  # siempre 0 (no hay condición "a favor")
            criterio_total_fijo=1102,
        ),
        seccion_ppt="Agentes - Workstations",
        destacado_ppt=True,
    ),
    Metrica(
        nombre="Workstations Retired",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Workstations_Retired-Details-*.xlsx",
        archivo_respaldo_patron="Workstations_Retired*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["AD Company"],
        criterios_incumplimiento=[],  # sin criterios -> todas las filas
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador="<", umbral=0.05,
            criterio_favor=[],
            criterio_total_fijo=1102,
        ),
        seccion_ppt="Agentes - Workstations",
        destacado_ppt=True,
    ),
    Metrica(
        nombre="Crowdstrike",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Detail-Details-*.xlsx",
        columna_id="Name",
        columnas_separacion=["Company"],
        criterios_incumplimiento=[
            [Condicion(columna="Crowdstrike", operador="igual", valor="Not deploy")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=1.0,
            criterio_favor=[[Condicion(columna="crowdstrike", operador="igual", valor="Deploy")]],
        ),
        seccion_ppt="Agentes - Workstations",
    ),
    Metrica(
        nombre="Qualys no cmdb",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Qualys-Workstations-Details-*.xlsx",
        columna_id="hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="In Qualys", operador="igual", valor="Not Deploy")]
        ],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="cmdb_ci_computer.xlsx", columna_base="hostname",
                            columna_cruzar="Name", columnas_extraer=["Name", "CI ID", "Status", "Status reason"]),
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="CI ID", operador="no_vacio", valor="")]],
        ),
        seccion_ppt="Agentes - Workstations",
        titulo_ppt="Qualys No cmdb",
        operaciones_ppt=[
            OperacionPPT(
                nombre="na",
                hoja_fuente="Qualys no cmdb",
                condicion=[[Condicion(columna="Name", operador="vacio", valor="")]],
            ),
            OperacionPPT(
                nombre="compliant",
                hoja_fuente="Qualys no cmdb",
                condicion=[[Condicion(columna="in qualys", operador="no_vacio", valor="")]],
            ),
        ],
    ),
    Metrica(
        nombre="Qualys cmdb",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=False,  # solo alimenta cumplimiento
        archivo_patron="Qualys-Workstations-Details-*.xlsx",
        columna_id="hostname",
        columnas_separacion=["company"],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="in qualys", operador="igual", valor="Deploy")]],
        ),
        seccion_ppt="Agentes - Workstations",
        titulo_ppt="Qualys cmdb",
    ),
    Metrica(
        nombre="Cobertura Qualys",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Agents Based-Details-*.xlsx",
        columna_id="hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="type", operador="igual", valor="Workstation"),
             Condicion(columna="deployment", operador="igual", valor="Failed")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.95,
            criterio_favor=[[Condicion(columna="type", operador="igual", valor="Workstation"),
                            Condicion(columna="deployment", operador="igual", valor="Passed")]],
            criterio_total=[[Condicion(columna="type", operador="igual", valor="Workstation")]],
        ),
        seccion_ppt="Agentes - Workstations",
        filtro_entidad={
            "BSNC": [[Condicion(columna="hostname", operador="contiene", valor="IOC")]],
        },
    ),
    Metrica(
        nombre="Netskope Workstations",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Windows-Deployment-Details-*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Deploy Text", operador="igual", valor="Not Deploy")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="deploy text", operador="igual", valor="Deploy")]],
        ),
        seccion_ppt="Agentes - Workstations",
        titulo_ppt="Netskope Workstations:",
    ),
    Metrica(
        nombre="Netskope PC virtuales",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Cloud-PCs-Deployment-Details-*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Deploy Text", operador="igual", valor="Not Deploy")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="deploy text", operador="igual", valor="Deploy")]],
            criterio_total=[[Condicion(columna="hostname", operador="contiene", valor="SANCO")]],
        ),
        seccion_ppt="Agentes - Workstations",
        titulo_ppt="Netskope Virtuales:",
    ),
    Metrica(
        nombre="DLP Netskope",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Devices_Export_*.csv",
        columna_id="Hostname",
        columnas_separacion=["company_softerra"],
        criterios_incumplimiento=[
            [Condicion(columna="Endpoint_DLP_Status", operador="igual", valor="Disabled")]
        ],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="softerra.xlsx", columna_base="user",
                            columna_cruzar="mail", columnas_extraer=["company_softerra"]),
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="Endpoint_DLP_Status", operador="igual", valor="Enabled")]],
        ),
        seccion_ppt="Agentes - Workstations",
        titulo_ppt="DLP Netskope:",
    ),
    Metrica(
        nombre="Cifrado",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Workstation-Encryption-Details-*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Encription", operador="igual", valor="No")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="encription", operador="igual", valor="Yes")]],
        ),
        seccion_ppt="Herramientas - Workstations",
        titulo_ppt="Cifrado:",
    ),
    Metrica(
        nombre="Push security",
        categoria="Workstations",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Push-Security-Deployment-Details-*.xlsx",
        columna_id="Hostname",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="push security enabled", operador="igual", valor="No")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="push security enabled", operador="igual", valor="Yes")]],
        ),
        seccion_ppt="Herramientas - Workstations",
        titulo_ppt="Push Security:",
    ),
    Metrica(
        nombre="Windows hello",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Cloud_Authentication_Non_Phishing_PasswordLess-Details-*.xlsx",
        columna_id="User Principal Name",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Registered Methods", operador="no_contiene", valor="hello")]
        ],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="USER.xlsx", columna_base="User Principal Name",
                            columna_cruzar="CF - ESI - ESP Local Id", columnas_extraer=["Job Profile"],
                            texto_a_quitar_del_base="@ucloud.santandergroup.net"),
            CRUCE_SOFTERRA_POR_EMPLEADO,
            Enriquecimiento(archivo_patron="DevicesWithInventory_*.csv", columna_base="User Principal Name",
                            columna_cruzar="primary user upn", columnas_extraer=["model"]),
            CRUCE_CMDB_POR_DESCRIPCION,
        ],
        criterios_limpieza=[
            [Condicion(columna="job profile", operador="contiene", valor="Customer Sales & Support")],
            [Condicion(columna="title", operador="contiene", valor="Customer Sales & Support")],
            [Condicion(columna="job profile", operador="contiene", valor="SANCO")],
            [Condicion(columna="model", operador="contiene", valor="SM-T")],
            [Condicion(columna="model", operador="contiene", valor="SM-X")],
            [Condicion(columna="model", operador="contiene", valor="Ipad")],
            [Condicion(columna="model", operador="contiene", valor="Iphone")],
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="registered methods", operador="contiene", valor="hello")]],
            excluir=[
                [Condicion(columna="job profile", operador="contiene", valor="Customer Sales & Support")],
                [Condicion(columna="title", operador="contiene", valor="Customer Sales & Support")],
                [Condicion(columna="job profile", operador="contiene", valor="SANCO")],
                [Condicion(columna="model", operador="contiene", valor="SM-T")],
                [Condicion(columna="model", operador="contiene", valor="SM-X")],
                [Condicion(columna="model", operador="contiene", valor="Ipad")],
                [Condicion(columna="model", operador="contiene", valor="Iphone")],
            ],
        ),
        seccion_ppt="Usuarios",
        grupo_visual_ppt="MFA",
        titulo_ppt="Windows Hello:",
    ),
    Metrica(
        nombre="MFA",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Cloud_Authentication_Non_Phishing_PasswordLess-Details-*.xlsx",
        columna_id="User Principal Name",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Registered Methods", operador="vacio", valor="")]
        ],
        enriquecimientos=[
            CRUCE_SOFTERRA_POR_EMPLEADO,
            CRUCE_CMDB_POR_DESCRIPCION,
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="registered methods", operador="no_vacio", valor="")]],
        ),
        seccion_ppt="Usuarios",
        grupo_visual_ppt="MFA",
        titulo_ppt="Registration:",
    ),
    Metrica(
        nombre="Ironchip",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="*UTC.csv",
        columna_id="username",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Status", operador="igual", valor="Invited")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="status", operador="distinto", valor="invited")]],
        ),
        seccion_ppt="Usuarios",
        grupo_visual_ppt="Ironchip",
    ),
    Metrica(
        nombre="Non-Phishing",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Cloud_Authentication_Non_Phishing_PasswordLess-Details-*.xlsx",
        columna_id="User Principal Name",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Non-Phishing Resistant Methods", operador="no_vacio", valor=""),
             Condicion(columna="Block Non-Phishing Resistant Methods", operador="igual", valor="No")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=1.0,
            criterio_favor=[
                [Condicion(columna="block non-phishing resistant methods", operador="igual", valor="yes")],
                [Condicion(columna="non-phishing resistant methods", operador="vacio", valor=""),
                 Condicion(columna="block non-phishing resistant methods", operador="igual", valor="no")],
            ],
        ),
        seccion_ppt="Usuarios",
        grupo_visual_ppt="SMS",
        titulo_ppt="Non-phishing Resistant",
    ),
    Metrica(
        nombre="Harmony Instalado",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Deploy-MTD-Android-iOS-Details-*.xlsx",
        columna_id="Username",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Harmony", operador="igual", valor="Not deploy")]
        ],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="USER.xlsx", columna_base="username",
                            columna_cruzar="CF - ESI - ESP Local Id",
                            columnas_extraer=["Legal Name", "Company - ID"]),
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.99,
            criterio_favor=[[Condicion(columna="harmony", operador="igual", valor="deploy")]],
        ),
        seccion_ppt="Antimalware - Dispositivos Moviles",
        titulo_ppt="Harmony (Protect) - Instalación",
    ),
    Metrica(
        nombre="MTD Sincronizado",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="Deploy-MTD-Android-iOS-Details-*.xlsx",
        columna_id="Username",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Status", operador="igual", valor="Not deploy")]
        ],
        enriquecimientos=[
            cruce_user_legal_name("username"),
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="status", operador="igual", valor="deploy")]],
        ),
        seccion_ppt="Antimalware - Dispositivos Moviles",
        titulo_ppt="Harmony (MTD) – No Sincroniza",
    ),
    Metrica(
        nombre="MTD Version",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="MTD-Client-Version-Details-*.xlsx",
        columna_id="Username",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["company"],
        criterios_incumplimiento=[
            [Condicion(columna="Client Version Update", operador="igual", valor="No")]
        ],
        enriquecimientos=[
            cruce_user_legal_name("username"),
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="client version update", operador="igual", valor="yes")]],
        ),
        seccion_ppt="Antimalware - Dispositivos Moviles",
        titulo_ppt="MTD client version",
    ),
    Metrica(
        nombre="Moviles Compliant",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=True,
        archivo_patron="DevicesWithInventory_*.csv",
        columna_id="primary user upn",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["Company - ID", "company_softerra"],
        criterios_incumplimiento=[
            [Condicion(columna="os", operador="no_contiene", valor="Windows")]
        ],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="softerra.xlsx", columna_base="Primary user email address",
                            columna_cruzar="mail", columnas_extraer=["company_softerra"]),
            Enriquecimiento(archivo_patron="USER.xlsx", columna_base="primary user upn",
                            columna_cruzar="CF - ESI - ESP Local Id", columnas_extraer=["Company - ID"],
                            texto_a_quitar_del_base="@ucloud.santandergroup.net"),
        ],
        funcion_especial="moviles_os_al_dia",
        criterios_limpieza=[
            [Condicion(columna="os al dia", operador="igual", valor="actualizado"),
             Condicion(columna="deprecado", operador="igual", valor="OK"),
             Condicion(columna="compliance", operador="igual", valor="Compliant")]
        ],
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="compliance", operador="distinto", valor="Noncompliant")]],
        ),
        seccion_ppt="Antimalware - Dispositivos Moviles",
        grupo_visual_ppt="Cumplimiento",
        titulo_ppt="Sincronización:",
    ),
    Metrica(
        nombre="Moviles Update",
        categoria="Dispositivos Móviles",
        obligatoria=True,
        incluir_en_reporte=False,  # solo alimenta cumplimiento
        archivo_patron="DevicesWithInventory_*.csv",
        columna_id="primary user upn",
        limpiar_id="@ucloud.santandergroup.net",
        columnas_separacion=["Company - ID", "company_softerra"],
        enriquecimientos=[
            Enriquecimiento(archivo_patron="softerra.xlsx", columna_base="Primary user email address",
                            columna_cruzar="mail", columnas_extraer=["company_softerra"]),
        ],
        funcion_especial="moviles_os_al_dia",
        cumplimiento=ConfigCumplimiento(
            aplica=True, operador=">", umbral=0.97,
            criterio_favor=[[Condicion(columna="os al dia",
                                       operador="igual", valor="actualizado")]],
            criterio_total=[[Condicion(columna="os", operador="no_contiene", valor="Windows")]],
        ),
        seccion_ppt="Antimalware - Dispositivos Moviles",
        grupo_visual_ppt="Update",
        titulo_ppt="Total:",
        operaciones_ppt=[
            OperacionPPT(
                nombre="IOS",
                hoja_fuente="Moviles Compliant",
                condicion=[[Condicion(columna="os", operador="contiene", valor="iOS"),
                           Condicion(columna="os al dia", operador="contiene", valor="desactualizado")]],
            ),
            OperacionPPT(
                nombre="Android",
                hoja_fuente="Moviles Compliant",
                condicion=[[Condicion(columna="os", operador="contiene", valor="Android"),
                           Condicion(columna="os al dia", operador="contiene", valor="desactualizado")]],
            ),
            OperacionPPT(
                nombre="update",
                hoja_fuente="Moviles Compliant",
                condicion=[[Condicion(columna="os al dia", operador="contiene", valor="desactualizado")]],
            ),
            OperacionPPT(
                nombre="noncomply",
                hoja_fuente="Moviles Compliant",
                condicion=[[Condicion(columna="compliance", operador="contiene", valor="Noncompliant")]],
            ),
        ],
    ),
]


def main():
    for metrica in METRICAS:
        existente = repo.obtener_por_nombre(metrica.nombre)
        if existente:
            repo.actualizar(existente.id, metrica)
            print(f"  🔄 Actualizada: {metrica.nombre}")
        else:
            repo.crear(metrica)
            print(f"  ✅ Creada: {metrica.nombre}")
    print(f"\nListo. {len(METRICAS)} métrica(s) procesada(s).")


if __name__ == "__main__":
    main()