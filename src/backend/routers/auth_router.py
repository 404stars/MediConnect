import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError
from database.connection import get_db
from models import Usuario
from schemas import (UserRegisterSchema, UserLoginSchema, TokenResponseSchema, MessageResponseSchema, ResetPasswordSchema)
from utils import (verify_password, get_current_user_id, get_user_roles)
from services import (create_access_token, invalidate_user_sessions, create_session, UsuarioService, PasswordService)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")
class EmailRequest(BaseModel):
    email: str

@router.post("/recuperar-password")
async def solicitar_recuperacion_password(request: EmailRequest, db: Session = Depends(get_db)):
    password_service = PasswordService(db)
    return await password_service.solicitar_recuperacion(request.email)

@router.post("/restablecer-password")
async def restablecer_password(datos: ResetPasswordSchema, db: Session = Depends(get_db)):
    password_service = PasswordService(db)
    return await password_service.restablecer_password(datos.token, datos.nueva_password)

@router.post("/register", response_model=MessageResponseSchema)
def register_user(user_data: UserRegisterSchema, db: Session = Depends(get_db)):
    try:
        usuario_service = UsuarioService(db)
        
        nuevo_usuario = usuario_service.crear_usuario_completo(
            rut=user_data.rut,
            nombre=user_data.nombre,
            apellido_paterno=user_data.apellido_paterno,
            apellido_materno=user_data.apellido_materno,
            email=user_data.email,
            telefono=user_data.telefono,
            password=user_data.password,
            roles_ids=None
        )
        
        return MessageResponseSchema(
            message="Usuario registrado exitosamente", 
            user_id=nuevo_usuario.id_usuario
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
