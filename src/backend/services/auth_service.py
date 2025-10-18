import jwt
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.usuario import Usuario
from models.sesion import Sesion
from utils.hashing import verify_password
from config import settings

logger = logging.getLogger(__name__)

def authenticate_user(db: Session, rut: str, password: str):
    user = db.query(Usuario).filter(Usuario.rut == rut).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hash_password):
        return None
    
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    jti = str(uuid.uuid4())
    to_encode.update({"jti": jti})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def invalidate_user_sessions(db: Session, user_id: int):
    db.query(Sesion).filter(
        Sesion.id_usuario == user_id,
        Sesion.activa == True
    ).update({"activa": False})
    db.commit()

def create_session(db: Session, user_id: int, token: str, jti: str):
    expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_session = Sesion(
        id_sesion=jti,
        id_usuario=user_id,
        token_jwt=token,
        fecha_creacion=datetime.utcnow(),
        fecha_expiracion=expires_at,
        activa=True
    )
    db.add(new_session)
    db.commit()
    return new_session
