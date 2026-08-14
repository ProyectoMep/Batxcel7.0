"""Script de una sola vez: crea/actualiza en data/filas_acta.json las 22
filas de la tabla de métricas del acta. Los textos de descripción y
glosario están tomados de tu acta real (Acta de seguimiento Workstations
BSNC), para que el acta generada se vea igual de completa desde el
primer día.

Ejecutar desde la raíz del proyecto: python scripts/seed_filas_acta.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.fila_acta import FilaActa, FilaActaRepository

repo = FilaActaRepository()

FILAS = [
    FilaActa(
        metrica_acta="Push Security", hoja="Push security",
        descripcion_sufijo="la cantidad de workstations sin la herramienta habilitada con respecto a la semana pasada.",
        accion_con_gestion="Revisar workstations que no la tengan.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Herramienta de seguridad para el navegador. Detecta amenazas como phishing y session "
                "hijacking en tiempo real. Se reporta cuando una Workstation no tiene Push Security habilitado.",
    ),
    FilaActa(
        metrica_acta="DLP Netskope", hoja="DLP Netskope",
        descripcion_sufijo="la cantidad de workstations sin el agente DLP desplegado con respecto a la semana pasada.",
        accion_con_gestion="Revisar workstations sin el agente DLP desplegado.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Prevención de pérdida de datos mediante Netskope. Se reporta cuando el módulo DLP de "
                "Netskope está desactivado en el equipo.",
    ),
    FilaActa(
        metrica_acta="Cifrado", hoja="Cifrado",
        descripcion_sufijo="la cantidad de workstations sin ningún tipo de cifrado configurado con respecto a la semana pasada.",
        accion_con_gestion="Solicitar a EUT España despliegue con BitLocker.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Por medio de SCCM se proporcionan opciones de cifrado para los datos de la empresa. "
                "Se reporta cuando la máquina no tiene ningún tipo de cifrado configurado.",
    ),
    FilaActa(
        metrica_acta="Crowdstrike", hoja="Crowdstrike",
        descripcion_sufijo="la cantidad de workstations sin la plataforma con respecto a la semana pasada.",
        accion_con_gestion="Validar despliegue del agente Crowdstrike.",
        accion_sin_gestion="Sin acción adicional. Actualmente todas las máquinas están cubiertas con el antimalware.",
        glosario="Plataforma de seguridad en la nube que utiliza inteligencia artificial para detectar, "
                "prevenir y responder amenazas en tiempo real. Se reporta cuando no está desplegada en una Workstation.",
    ),
    FilaActa(
        metrica_acta="Netskope Workstations", hoja="Netskope Workstations",
        descripcion_sufijo="la cantidad de workstations sin la plataforma habilitada con respecto a la semana pasada.",
        accion_con_gestion="Validar despliegue de Netskope en las Workstations reportadas.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Plataforma que protege datos y aplicaciones en la nube. Se reporta cuando no está "
                "desplegada en la Workstation o PC virtual.",
    ),
    FilaActa(
        metrica_acta="Netskope Virtuales", hoja="Netskope PC virtuales",
        descripcion_sufijo="la cantidad de PC Cloud sin la plataforma habilitada con respecto a la semana pasada.",
        accion_con_gestion="Validar despliegue de Netskope en las PC virtuales reportadas.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Plataforma que protege datos y aplicaciones en la nube. Se reporta cuando no está "
                "desplegada en la Workstation o PC virtual.",
    ),
    FilaActa(
        metrica_acta="High Risk Software", hoja="High Risk Software",
        descripcion_sufijo="software de alto riesgo identificado en las workstations reportadas.",
        accion_con_gestion="Gestionar la desinstalación del software de alto riesgo reportado.",
        accion_sin_gestion="Sin acción pendiente. No se ha identificado software de alto riesgo.",
        glosario="Indica si dentro de la workstation hay instalado algún software de alto riesgo.",
    ),
    FilaActa(
        metrica_acta="Qualys No CMDB", hoja="Qualys no cmdb", operacion="na",
        descripcion_sufijo="la cantidad de workstations que se encuentran en Qualys pero no en CMDB.",
        accion_con_gestion="Gestionar el registro en CMDB de los equipos sin coincidencia.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Equipo con agente Qualys instalado pero sin registro en CMDB. Se debe crear el CI "
                "(Elemento de Configuración) en la CMDB.",
    ),
    FilaActa(
        metrica_acta="Qualys CMDB", hoja="Qualys no cmdb",
        descripcion_sufijo="la cantidad de workstations reportadas por Qualys con respecto a la semana pasada.",
        accion_con_gestion="Gestionar el despliegue del agente Qualys en los equipos reportados.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Equipo con agente Qualys y en CMDB. Se debe categorizar correctamente con la "
                "etiqueta de Colombia.",
    ),
    FilaActa(
        metrica_acta="Cobertura Qualys", hoja="Cobertura Qualys",
        descripcion_sufijo="la cantidad de workstations con fallo de despliegue del agente Qualys.",
        accion_con_gestion="Continuar gestionando con Área Soporte.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Mide la cantidad de estaciones de trabajo con el agente Qualys instalado y "
                "comunicación con la consola en los últimos 21 días.",
    ),
    FilaActa(
        metrica_acta="Workstations Retired", hoja="Workstations Retired",
        descripcion_sufijo="la cantidad de workstations retiradas con respecto a la semana pasada.",
        accion_con_gestion="Solicitar eliminación de Hostnames y purgado en Qualys semanalmente.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Workstations retiradas de la organización. Se reportan según el documento de "
                "detalle de máquinas.",
    ),
    FilaActa(
        metrica_acta="Non-Phishing Resistant", hoja="Non-Phishing",
        descripcion_sufijo="la cantidad de dispositivos con métodos no resistentes a phishing con respecto a la semana pasada.",
        accion_con_gestion="Agregar a los usuarios a los grupos de bloqueo de métodos no resistentes a phishing.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Usuarios con al menos un método no resistente a phishing (SMS o llamada telefónica) "
                "registrado en MFA.",
    ),
    FilaActa(
        metrica_acta="MFA – Windows Hello", hoja="Windows hello",
        descripcion_sufijo="la cantidad de dispositivos sin configuración de Windows Hello. Excepción aplicada a S3 Caceis y SANCO.",
        accion_con_gestion="Contactar usuarios para configurar huella, PIN o rostro. Validar usuarios sin equipo.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Herramienta de autenticación por reconocimiento facial, huella digital o PIN. Se "
                "reporta cuando no está registrada. Excepción: tablets S3 Caceis y virtuales SANCO.",
    ),
    FilaActa(
        metrica_acta="MFA – Registration", hoja="MFA",
        descripcion_sufijo="la cantidad de usuarios sin método MFA configurado. Requiere apoyo y gestión rápida. No se permite SMS ni Voz.",
        accion_con_gestion="Configurar algún método (IronChip, Authenticator, FIDOKey o WHFB).",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Autenticación multifactor. Se reporta cuando el usuario no tiene ningún método MFA "
                "registrado. No aplica a usuarios sin equipo.",
    ),
    FilaActa(
        metrica_acta="Ironchip", hoja="Ironchip",
        descripcion_sufijo="la cantidad de usuarios sin Ironchip configurado.",
        accion_con_gestion="Gestionar el listado de usuarios pendientes por configurar.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Plataforma de autenticación por ubicación inteligente. Se reporta cuando el estado "
                "contiene la palabra 'invitado'.",
    ),
    FilaActa(
        metrica_acta="Harmony (Protect)", hoja="Harmony Instalado",
        descripcion_sufijo="la cantidad de dispositivos sin el antimalware instalado con respecto a la semana pasada.",
        accion_con_gestion="Gestionar la instalación de Harmony en los dispositivos reportados.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Solución de seguridad para dispositivos móviles. Se reporta cuando no está instalada "
                "en el dispositivo.",
    ),
    FilaActa(
        metrica_acta="Harmony (MTD)", hoja="MTD Sincronizado",
        descripcion_sufijo="la cantidad de dispositivos no sincronizados con respecto a la semana pasada.",
        accion_con_gestion="Contactar usuarios para abrir la app y realizar escaneo.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Defensa contra amenazas móviles. Se reporta cuando el dispositivo no ha realizado "
                "escaneo en la plataforma.",
    ),
    FilaActa(
        metrica_acta="MTD Client Version", hoja="MTD Version",
        descripcion_sufijo="la cantidad de dispositivos sin la última versión disponible del MTD con respecto a la semana pasada.",
        accion_con_gestion="Garantizar que todos tengan la versión más reciente del grupo.",
        accion_sin_gestion="Sin acción adicional.",
        glosario="Se reporta cuando el antimalware móvil no está en la última versión disponible para el grupo.",
    ),
    FilaActa(
        metrica_acta="Update Móviles iOS", hoja="Moviles Compliant", operacion="IOS",
        descripcion_sufijo="la cantidad de dispositivos iOS sin la última actualización disponible con respecto a la semana pasada.",
        accion_con_gestion="Contactar usuarios iOS para actualizar el sistema operativo.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Dispositivos móviles sin la última actualización de sistema operativo disponible.",
    ),
    FilaActa(
        metrica_acta="Update Móviles Android", hoja="Moviles Compliant", operacion="Android",
        descripcion_sufijo="la cantidad de dispositivos Android sin la última actualización disponible con respecto a la semana pasada.",
        accion_con_gestion="Contactar usuarios Android para actualizar el sistema operativo.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Dispositivos móviles sin la última actualización de sistema operativo disponible.",
    ),
    FilaActa(
        metrica_acta="Total Update Móviles", hoja="Moviles Compliant", operacion="update",
        descripcion_sufijo="la cantidad de dispositivos móviles sin la última actualización disponible con respecto a la semana pasada.",
        accion_con_gestion="Contactar todos los usuarios para actualizar el sistema operativo.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Total de dispositivos móviles sin la última actualización de sistema operativo disponible.",
    ),
    FilaActa(
        metrica_acta="Móviles Compliance", hoja="Moviles Compliant", operacion="noncomply",
        descripcion_sufijo="la cantidad de dispositivos en estado 'Noncompliant' con respecto a la semana pasada.",
        accion_con_gestion="Revisar estado, sincronizar Intune y escanear con Harmony.",
        accion_sin_gestion="Sin acción pendiente.",
        glosario="Dispositivos en estado 'Noncompliant' en Intune. Requiere revisión, sincronización "
                "y escaneo con Harmony.",
    ),
]


def main():
    for indice, fila in enumerate(FILAS):
        fila.orden = indice
        existente = None
        for f in repo.listar():
            if f.metrica_acta.strip().lower() == fila.metrica_acta.strip().lower():
                existente = f
                break
        if existente:
            repo.actualizar(existente.id, fila)
            print(f"  🔄 Actualizada: {fila.metrica_acta}")
        else:
            repo.crear(fila)
            print(f"  ✅ Creada: {fila.metrica_acta}")
    print(f"\nListo. {len(FILAS)} fila(s) de acta procesada(s).")


if __name__ == "__main__":
    main()