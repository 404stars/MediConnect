import logging
from datetime import date, time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

def obtener_configuracion_email():
    return {
        "server": settings.MAIL_SERVER,
        "port": settings.MAIL_PORT,
        "username": settings.MAIL_USERNAME,
        "password": settings.MAIL_PASSWORD,
        "from_email": settings.MAIL_FROM,
        "use_tls": settings.MAIL_USE_TLS,
        "use_ssl": settings.MAIL_USE_SSL
    }

def formatear_fecha(fecha: date) -> str:
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    return f"{fecha.day} de {meses[fecha.month]} de {fecha.year}"

def formatear_hora(hora: time) -> str:
    return hora.strftime("%H:%M")

def renderizar_plantilla(template_name: str, **context) -> str:
    """
    Renderiza una plantilla de email con el contexto proporcionado.
    
    Args:
        template_name: Nombre del archivo de plantilla (ej: "confirmacion_cita.html")
        **context: Variables a pasar a la plantilla
    
    Returns:
        HTML renderizado como string
    """
    try:
        template = jinja_env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error al renderizar plantilla {template_name}: {str(e)}")
        raise

async def enviar_correo_confirmacion(
    email: str,
    nombre: str,
    fecha: date,
    hora: time,
    profesional: str,
    especialidad: str
) -> bool:
    try:
        fecha_formateada = formatear_fecha(fecha)
        hora_formateada = formatear_hora(hora)
        
        mail_config = obtener_configuracion_email()
        logger.info(f"[EMAIL] Configuración utilizada: {mail_config}")

        # Renderizar la plantilla con los datos
        html_body = renderizar_plantilla(
            "confirmacion_cita.html",
            titulo="Cita Confirmada",
            color_tema="#4CAF50",
            nombre=nombre,
            fecha_formateada=fecha_formateada,
            hora_formateada=hora_formateada,
            profesional=profesional,
            especialidad=especialidad
        )
        
        mensaje = MessageSchema(
            subject=f"Cita Confirmada - {fecha_formateada}",
            recipients=[email],
            body=html_body,
            subtype="html"
        )
        conf = ConnectionConfig(
            MAIL_USERNAME=mail_config["username"],
            MAIL_PASSWORD=mail_config["password"],
            MAIL_FROM=mail_config["from_email"],
            MAIL_PORT=mail_config["port"],
            MAIL_SERVER=mail_config["server"],
            MAIL_STARTTLS=mail_config["use_tls"],
            MAIL_SSL_TLS=mail_config["use_ssl"],
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(mensaje)
            logger.info(f"Correo de confirmación enviado exitosamente a {email}")
            return True
        except Exception as smtp_error:
            logger.error(f"[EMAIL] Error SMTP al enviar correo a {email}: {smtp_error}")
            raise
        
    except Exception as e:
        logger.error(f"Error al enviar correo de confirmación a {email}: {str(e)}")
        return False

async def enviar_correo_cancelacion(
    email: str,
    nombre: str,
    fecha: date,
    hora: time,
    profesional: str,
    motivo_cancelacion: str
) -> bool:
    try:
        fecha_formateada = formatear_fecha(fecha)
        hora_formateada = formatear_hora(hora)
        
        mail_config = obtener_configuracion_email()
        logger.info(f"[EMAIL] Configuración utilizada: {mail_config}")

        # Renderizar la plantilla con los datos
        html_body = renderizar_plantilla(
            "cancelacion_cita.html",
            titulo="Cita Cancelada",
            color_tema="#dc3545",
            nombre=nombre,
            fecha_formateada=fecha_formateada,
            hora_formateada=hora_formateada,
            profesional=profesional,
            motivo_cancelacion=motivo_cancelacion
        )
        
        mensaje = MessageSchema(
            subject=f"Cita Cancelada - {fecha_formateada}",
            recipients=[email],
            body=html_body,
            subtype="html"
        )
        conf = ConnectionConfig(
            MAIL_USERNAME=mail_config["username"],
            MAIL_PASSWORD=mail_config["password"],
            MAIL_FROM=mail_config["from_email"],
            MAIL_PORT=mail_config["port"],
            MAIL_SERVER=mail_config["server"],
            MAIL_STARTTLS=mail_config["use_tls"],
            MAIL_SSL_TLS=mail_config["use_ssl"],
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(mensaje)
            logger.info(f"Correo de cancelación enviado exitosamente a {email}")
            return True
        except Exception as smtp_error:
            logger.error(f"[EMAIL] Error SMTP al enviar correo a {email}: {smtp_error}")
            raise
        
    except Exception as e:
        logger.error(f"Error al enviar correo de cancelación a {email}: {str(e)}")
        return False

async def enviar_correo_reprogramacion(
    email: str,
    nombre: str,
    fecha: date,
    hora: time,
    profesional: str,
    especialidad: str,
    fecha_anterior: date,
    hora_anterior: time
) -> bool:
    try:
        fecha_formateada = formatear_fecha(fecha)
        fecha_anterior_formateada = formatear_fecha(fecha_anterior)
        hora_formateada = formatear_hora(hora)
        hora_anterior_formateada = formatear_hora(hora_anterior)
        
        mail_config = obtener_configuracion_email()
        logger.info(f"[EMAIL] Configuración utilizada: {mail_config}")
        
        html_body = renderizar_plantilla(
            "reprogramacion_cita.html",
            titulo="Cita Reprogramada",
            color_tema="#2196F3",
            nombre=nombre,
            fecha_formateada=fecha_formateada,
            hora_formateada=hora_formateada,
            profesional=profesional,
            especialidad=especialidad,
            fecha_anterior_formateada=fecha_anterior_formateada,
            hora_anterior_formateada=hora_anterior_formateada
        )
        
        mensaje = MessageSchema(
            subject=f"Cita Reprogramada - {fecha_formateada}",
            recipients=[email],
            body=html_body,
            subtype="html"
        )
        conf = ConnectionConfig(
            MAIL_USERNAME=mail_config["username"],
            MAIL_PASSWORD=mail_config["password"],
            MAIL_FROM=mail_config["from_email"],
            MAIL_PORT=mail_config["port"],
            MAIL_SERVER=mail_config["server"],
            MAIL_STARTTLS=mail_config["use_tls"],
            MAIL_SSL_TLS=mail_config["use_ssl"],
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(mensaje)
            logger.info(f"Correo de reprogramación enviado exitosamente a {email}")
            return True
        except Exception as smtp_error:
            logger.error(f"[EMAIL] Error SMTP al enviar correo a {email}: {smtp_error}")
            raise
    except Exception as e:
        logger.error(f"Error general al enviar correo de reprogramación a {email}: {str(e)}")
        return False

async def enviar_correo_recuperacion_password(
    email: str,
    nombre: str,
    enlace_recuperacion: str
) -> bool:
    try:
        mail_config = obtener_configuracion_email()
        logger.info(f"[EMAIL] Configuración utilizada: {mail_config}")
        
        # Renderizar la plantilla con los datos
        html_body = renderizar_plantilla(
            "recuperacion_password.html",
            titulo="Recuperación de Contraseña",
            color_tema="#FF9800",
            nombre=nombre,
            enlace_recuperacion=enlace_recuperacion
        )
        
        mensaje = MessageSchema(
            subject="Recuperación de Contraseña - MediConnect",
            recipients=[email],
            body=html_body,
            subtype="html"
        )
        
        conf = ConnectionConfig(
            MAIL_USERNAME=mail_config["username"],
            MAIL_PASSWORD=mail_config["password"],
            MAIL_FROM=mail_config["from_email"],
            MAIL_PORT=mail_config["port"],
            MAIL_SERVER=mail_config["server"],
            MAIL_STARTTLS=mail_config["use_tls"],
            MAIL_SSL_TLS=mail_config["use_ssl"],
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        try:
            fm = FastMail(conf)
            await fm.send_message(mensaje)
            logger.info(f"Correo de recuperación enviado exitosamente a {email}")
            return True
        except Exception as smtp_error:
            logger.error(f"[EMAIL] Error SMTP al enviar correo de recuperación a {email}: {smtp_error}")
            raise
            
    except Exception as e:
        logger.error(f"Error general al enviar correo de recuperación de contraseña a {email}: {str(e)}")
        return False

async def enviar_correo_confirmacion_cambio_password(
    email: str,
    nombre: str
) -> bool:
    try:
        mail_config = obtener_configuracion_email()
        logger.info(f"[EMAIL] Enviando confirmación de cambio de contraseña a {email}")
        
        html_body = renderizar_plantilla(
            "confirmacion_cambio_password.html",
            titulo="Contraseña Cambiada",
            color_tema="#28a745",
            nombre=nombre
        )
        
        mensaje = MessageSchema(
            subject="Contraseña Cambiada Exitosamente - MediConnect",
            recipients=[email],
            body=html_body,
            subtype="html"
        )
        
        conf = ConnectionConfig(
            MAIL_USERNAME=mail_config["username"],
            MAIL_PASSWORD=mail_config["password"],
            MAIL_FROM=mail_config["from_email"],
            MAIL_PORT=mail_config["port"],
            MAIL_SERVER=mail_config["server"],
            MAIL_STARTTLS=mail_config["use_tls"],
            MAIL_SSL_TLS=mail_config["use_ssl"],
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        
        try:
            fm = FastMail(conf)
            await fm.send_message(mensaje)
            logger.info(f"Correo de confirmación de cambio de contraseña enviado exitosamente a {email}")
            return True
        except Exception as smtp_error:
            logger.error(f"[EMAIL] Error SMTP al enviar confirmación a {email}: {smtp_error}")
            raise
            
    except Exception as e:
        logger.error(f"Error general al enviar confirmación de cambio de contraseña a {email}: {str(e)}")
        return False
