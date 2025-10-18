import logging
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.usuario_rol import UsuarioRol
from models.rol import Rol
from models.usuario import Usuario
from utils.auth_dependencies import get_current_user_id
from typing import List

logger = logging.getLogger(__name__)

def get_user_roles_with_permissions(db: Session, user_id: int):
    roles = db.query(Rol).join(UsuarioRol).filter(UsuarioRol.id_usuario == user_id).all()
    
    user_permissions = set()
    role_names = []
    
    for role in roles:
        role_names.append(role.nombre)
        if role.permisos:
            permissions = [p.strip() for p in role.permisos.split(',')]
            user_permissions.update(permissions)
    
    return role_names, list(user_permissions)

def get_user_roles(db: Session, user_id: int):
    role_names, _ = get_user_roles_with_permissions(db, user_id)
    return role_names

def has_permission(user_id: int, permission: str, db: Session):
    _, user_permissions = get_user_roles_with_permissions(db, user_id)
    return permission in user_permissions

def has_any_role(user_id: int, roles: List[str], db: Session) -> bool:
    user_roles = get_user_roles(db, user_id)
    return any(role in user_roles for role in roles)

def require_permission(permission: str):
    def dependency(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        if not has_permission(current_user_id, permission, db):
            raise HTTPException(status_code=403, detail="Permiso denegado")
        return current_user_id
    return dependency

def require_roles(roles: List[str]):
    def dependency(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        if not has_any_role(current_user_id, roles, db):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return current_user_id
    return dependency

def require_any_role(roles: List[str]):
    """Decorador que permite acceso si el usuario tiene cualquiera de los roles especificados"""
    def dependency(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
        user_roles = get_user_roles(db, current_user_id)
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=403, 
                detail=f"Requiere uno de los siguientes roles: {', '.join(roles)}"
            )
        return current_user_id
    return dependency

def require_admin(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not has_any_role(current_user_id, ["Administrador"], db):
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requieren permisos de administrador")
    return current_user_id

def require_staff(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if not has_any_role(current_user_id, ["Administrador", "Médico", "Recepcionista"], db):
        raise HTTPException(status_code=403, detail="Acceso denegado: Se requiere ser personal del sistema")
    return current_user_id
