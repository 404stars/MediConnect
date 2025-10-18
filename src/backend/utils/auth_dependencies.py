import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.connection import get_db
from models.sesion import Sesion
from models.usuario import Usuario
from services.auth_service import verify_token

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: no contiene user ID")
        
        session = db.query(Sesion).filter(
            Sesion.id_sesion == payload.get("jti"), 
            Sesion.activa == True
        ).first()
        
        if not session:
            raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
        
        return int(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="ID de usuario inválido")
    except Exception as e:
        logger.error(f"Error inesperado en auth: {e}")
        raise HTTPException(status_code=401, detail="Error de autenticación")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Usuario:
    user_id = get_current_user_id(credentials, db)
    
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    if user.estado != "ACTIVO":
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    return user
