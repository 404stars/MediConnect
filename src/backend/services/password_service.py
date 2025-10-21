import logging
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.usuario import Usuario
from utils.hashing import hash_password
from utils.email_utils import enviar_correo_recuperacion_password, enviar_correo_confirmacion_cambio_password
from services.auth_service import invalidate_user_sessions
from config import settings

logger = logging.getLogger(__name__)


class PasswordService:
    TOKEN_EXPIRACION_MINUTOS = 30
    
    def __init__(self, db: Session):
        self.db = db
    
    async def solicitar_recuperacion(self, email: str):
        logger.info(f"Solicitud de recuperación para email: {email}")
        
        usuario = self.db.query(Usuario).filter(Usuario.email == email).first()
        
        if usuario:
            logger.info(f"Usuario encontrado: {usuario.nombre}")
            
            token = secrets.token_urlsafe(32)
            expiracion = datetime.utcnow() + timedelta(minutes=self.TOKEN_EXPIRACION_MINUTOS)
            
            usuario.token_recuperacion = token
            usuario.expiracion_token = expiracion
            self.db.commit()
            
            enlace = f"{settings.FRONTEND_URL}/restablecer-password?token={token}"
            
            try:
                success = await enviar_correo_recuperacion_password(email, usuario.nombre, enlace)
                if success:
                    logger.info("Correo enviado exitosamente")
                else:
                    logger.warning("Error al enviar correo")
            except Exception as e:
                logger.error(f"Error al enviar correo: {e}")
        else:
            logger.info("Usuario no encontrado")
        
        return {"message": "Correo de recuperación enviado si el email está registrado"}
    
    async def restablecer_password(self, token: str, nueva_password: str):
        try:
            logger.info(f"Restableciendo contraseña para token: {token[:10]}...")
            
            usuario = self.db.query(Usuario).filter(
                Usuario.token_recuperacion == token,
                Usuario.expiracion_token >= datetime.utcnow()
            ).first()
            
            if not usuario:
                logger.warning("Token inválido o expirado")
                raise HTTPException(status_code=400, detail="Token inválido o expirado")
            
            nuevo_hash = hash_password(nueva_password)
            
            usuario.hash_password = nuevo_hash
            usuario.token_recuperacion = None
            usuario.expiracion_token = None
            
            invalidate_user_sessions(self.db, usuario.id_usuario)
            
            self.db.commit()
            self.db.refresh(usuario)
            
            logger.info("Contraseña actualizada exitosamente")
            
            try:
                await enviar_correo_confirmacion_cambio_password(
                    email=usuario.email,
                    nombre=usuario.nombre
                )
                logger.info(f"Correo de confirmación enviado a {usuario.email}")
            except Exception as email_error:
                logger.warning(f"No se pudo enviar el correo de confirmación: {str(email_error)}")
            
            return {"message": "Contraseña restablecida exitosamente"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error inesperado en restablecimiento: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Error interno del servidor")
