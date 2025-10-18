from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional, List

class AdminCreateUserSchema(BaseModel):
    rut: str = Field(..., min_length=8, max_length=12)
    nombre: str = Field(..., min_length=2, max_length=50)
    apellido_paterno: str = Field(..., min_length=2, max_length=50)
    apellido_materno: Optional[str] = Field(None, max_length=50)
    email: EmailStr
    telefono: Optional[str] = Field(None, min_length=8, max_length=15)
    password: str = Field(..., min_length=6, max_length=128)
    roles: List[int] = Field(default_factory=list)
    
    @field_validator('rut')
    @classmethod
    def validate_rut(cls, v):
        clean_rut = re.sub(r'[.\s-]', '', v.strip())
        
        if len(clean_rut) < 8 or len(clean_rut) > 9:
            raise ValueError('RUT debe tener entre 7 y 8 dígitos más el dígito verificador')
        
        rut_number = clean_rut[:-1]
        dv = clean_rut[-1].upper()
        
        if not rut_number.isdigit():
            raise ValueError('RUT debe contener solo números')
        
        if not re.match(r'^[0-9kK]$', dv):
            raise ValueError('Dígito verificador debe ser un número o K')
        
        formatted_rut = f"{rut_number}-{dv}"
        return formatted_rut
    
    @field_validator('nombre', 'apellido_paterno')
    @classmethod
    def validate_required_names(cls, v):
        if v is None or v == "":
            raise ValueError('Este campo es obligatorio')
        v_clean = v.strip()
        if not v_clean:
            raise ValueError('Este campo es obligatorio')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', v_clean):
            raise ValueError('Solo se permiten letras y espacios')
        return v_clean.title()
    
    @field_validator('apellido_materno')
    @classmethod
    def validate_apellido_materno(cls, v):
        if v is None or v == "":
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', v_clean):
            raise ValueError('Solo se permiten letras y espacios')
        return v_clean.title()
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        if v is None or v == "":
            return None
        v_clean = v.strip()
        if not v_clean:
            return None
        if not re.match(r'^[\+]?[0-9\-\s\(\)]+$', v_clean):
            raise ValueError('Teléfono debe contener solo números y caracteres +, -, espacios, ( )')
        return v_clean
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

class UpdateUserRolesSchema(BaseModel):
    user_id: int
    roles: List[int]
class UserRoleSchema(BaseModel):
    id_rol: int
    nombre: str

class UserListItemSchema(BaseModel):
    id_usuario: int
    rut: str
    nombre: str
    apellido_paterno: str
    apellido_materno: Optional[str]
    email: str
    telefono: Optional[str]
    roles: List[UserRoleSchema]

class RoleSchema(BaseModel):
    id_rol: int
    nombre: str
    descripcion: Optional[str]
    permisos: Optional[str] = None
    
    @property
    def permisos_list(self) -> List[str]:
        if self.permisos:
            return [p.strip() for p in self.permisos.split(',')]
        return []

class RoleCreateSchema(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=40)
    descripcion: Optional[str] = Field(None, max_length=200)
    permisos: List[str] = Field(default=[], description="Lista de permisos para el rol")

class RoleUpdateSchema(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=40)
    descripcion: Optional[str] = Field(None, max_length=200)
    permisos: Optional[List[str]] = Field(None)

class UsersListResponseSchema(BaseModel):
    users: List[UserListItemSchema]
    total: int

class RolesListResponseSchema(BaseModel):
    roles: List[RoleSchema]
