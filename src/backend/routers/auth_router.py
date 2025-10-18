import logging
import secrets
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError
from config import settings
from database.connection import get_db
from models.usuario import Usuario
from models.usuario_rol import UsuarioRol
from models.rol import Rol
from models.paciente import Paciente
from models.funcionario import Funcionario
from models.profesional_salud import ProfesionalSalud
from schemas.auth_schemas import (UserRegisterSchema, UserLoginSchema, TokenResponseSchema, 
                                  MessageResponseSchema, UserResponseSchema, ResetPasswordSchema)
from utils.hashing import hash_password, verify_password
from utils.auth_dependencies import get_current_user_id
from utils.permissions import get_user_roles
from utils.constants import Rol as RolConstantes
from utils.email_utils import enviar_correo_recuperacion_password, enviar_correo_confirmacion_cambio_password
from services.auth_service import authenticate_user, create_access_token, invalidate_user_sessions, create_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")
class EmailRequest(BaseModel):
    email: str

@router.post("/recuperar-password")
async def solicitar_recuperacion_password(request: EmailRequest, db: Session = Depends(get_db)):
    """
    Optimizado: Función async desde el inicio para evitar conflictos de event loop
    """
    email = request.email
    logger.info(f"Solicitud de recuperación para email: {email}")
    
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        logger.info(f"Usuario encontrado: {usuario.nombre}")
        
        token = secrets.token_urlsafe(32)
        expiracion = datetime.utcnow() + timedelta(minutes=30)
        
        usuario.token_recuperacion = token
        usuario.expiracion_token = expiracion
        db.commit()
        
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

@router.post("/restablecer-password")
async def restablecer_password(datos: ResetPasswordSchema, db: Session = Depends(get_db)):
    """
    Optimizado: Query única que valida token y expiración en una sola consulta
    """
    try:
        logger.info(f"Restableciendo contraseña para token: {datos.token[:10]}...")
        
        # Query optimizada: valida token y expiración en una sola consulta
        usuario = db.query(Usuario).filter(
            Usuario.token_recuperacion == datos.token,
            Usuario.expiracion_token >= datetime.utcnow()
        ).first()
        
        if not usuario:
            logger.warning("Token inválido o expirado")
            raise HTTPException(status_code=400, detail="Token inválido o expirado")
        
        nuevo_hash = hash_password(datos.nueva_password)
        
        usuario.hash_password = nuevo_hash
        usuario.token_recuperacion = None
        usuario.expiracion_token = None
        
        invalidate_user_sessions(db, usuario.id_usuario)
        
        db.commit()
        db.refresh(usuario)
        
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
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/register", response_model=MessageResponseSchema)
def register_user(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(Usuario).filter(
            (Usuario.rut == user_data.rut) | (Usuario.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.rut == user_data.rut:
                raise HTTPException(status_code=400, detail="Ya existe un usuario con este RUT")
            else:
                raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

        hashed_password = hash_password(user_data.password)
        new_user = Usuario(
            rut=user_data.rut,
            nombre=user_data.nombre,
            apellido_paterno=user_data.apellido_paterno,
            apellido_materno=user_data.apellido_materno or "",
            email=user_data.email,
            telefono=user_data.telefono,
            hash_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        paciente_role = db.query(Rol).filter(Rol.nombre == RolConstantes.PACIENTE).first()
        if paciente_role:
            user_role = UsuarioRol(id_usuario=new_user.id_usuario, id_rol=paciente_role.id_rol)
            db.add(user_role)
            
            
            nuevo_paciente = Paciente(id_usuario=new_user.id_usuario)
            db.add(nuevo_paciente)
            
            db.commit()
        
        return MessageResponseSchema(
            message="Usuario registrado exitosamente", 
            user_id=new_user.id_usuario
        )
        
    except ValidationError as e:
        
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        
        db.rollback()
        raise
    except Exception as e:
        
        db.rollback()
        print(f"Error inesperado en registro: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/login", response_model=TokenResponseSchema)
def login_user(credentials: UserLoginSchema, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting login for identifier: {credentials.identifier}")
        
        user = db.query(Usuario).filter(
            (Usuario.rut == credentials.identifier) | (Usuario.email == credentials.identifier)
        ).first()
        
        if not user:
            logger.warning("User not found")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        if not verify_password(credentials.password, user.hash_password):
            logger.warning("Password verification failed")
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        logger.info("Password verified successfully")
        
        invalidate_user_sessions(db, user.id_usuario)
        
        access_token, jti = create_access_token(data={"sub": str(user.id_usuario)})
        
        create_session(db, user.id_usuario, access_token, jti)
        
        user_response = {
            "id": user.id_usuario,
            "nombre": f"{user.nombre} {user.apellido_paterno}".strip(),
            "email": user.email,
            "rut": user.rut
        }
        
        return TokenResponseSchema(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.post("/logout", response_model=MessageResponseSchema)
def logout_user(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    try:
        invalidate_user_sessions(db, current_user_id)
        return MessageResponseSchema(message="Sesión cerrada exitosamente")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al cerrar sesión")

@router.get("/me/roles")
def get_my_roles(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    roles = get_user_roles(db, current_user_id)
    return {"roles": roles}

@router.get("/me/profile")
def get_my_profile(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id_usuario == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": user.id_usuario,
        "rut": user.rut,
        "nombre": user.nombre,
        "apellido_paterno": user.apellido_paterno,
        "apellido_materno": user.apellido_materno,
        "email": user.email,
        "telefono": user.telefono
    }

@router.put("/me/profile")
def update_my_profile(
    profile_data: dict,
    current_user_id: int = Depends(get_current_user_id), 
    db: Session = Depends(get_db)
):
    user = db.query(Usuario).filter(Usuario.id_usuario == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if "email" in profile_data and profile_data["email"] != user.email:
        existing_email = db.query(Usuario).filter(
            Usuario.email == profile_data["email"],
            Usuario.id_usuario != current_user_id
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
    
    allowed_fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'telefono']
    for field in allowed_fields:
        if field in profile_data:
            setattr(user, field, profile_data[field])
    
    try:
        db.commit()
        return {"message": "Perfil actualizado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar perfil")
