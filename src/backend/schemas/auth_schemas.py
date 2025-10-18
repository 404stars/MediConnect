from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional, Dict, Any
from datetime import date, datetime, time

class UserRegisterSchema(BaseModel):
    rut: str = Field(..., min_length=8, max_length=12, description="RUT del usuario")
    nombre: str = Field(..., min_length=2, max_length=50, description="Nombre del usuario")
    apellido_paterno: str = Field(..., min_length=2, max_length=50, description="Apellido paterno")
    apellido_materno: Optional[str] = Field(None, max_length=50, description="Apellido materno")
    email: EmailStr = Field(..., description="Email del usuario")
    telefono: Optional[str] = Field(None, min_length=8, max_length=15, description="Teléfono")
    password: str = Field(..., min_length=6, max_length=128, description="Contraseña")
    
    @field_validator('rut')
    @classmethod
    def validate_rut(cls, v):
        try:
            clean_rut = re.sub(r'[.\s-]', '', v.strip().upper())
            
            if len(clean_rut) < 8 or len(clean_rut) > 9:
                raise ValueError('RUT debe tener entre 7 y 8 dígitos más el dígito verificador')
            
            rut_number = clean_rut[:-1]
            dv = clean_rut[-1]
            
            if not rut_number.isdigit():
                raise ValueError('RUT debe contener solo números')
            
            if not re.match(r'^[0-9K]$', dv):
                raise ValueError('Dígito verificador debe ser un número del 0-9 o K')
            
            suma = 0
            multiplicador = 2
            
            for i in range(len(rut_number) - 1, -1, -1):
                suma += int(rut_number[i]) * multiplicador
                multiplicador = multiplicador + 1 if multiplicador < 7 else 2
            
            dv_calculado = 11 - (suma % 11)
            if dv_calculado == 11:
                dv_esperado = '0'
            elif dv_calculado == 10:
                dv_esperado = 'K'
            else:
                dv_esperado = str(dv_calculado)
            
            if dv != dv_esperado:
                raise ValueError('RUT inválido: dígito verificador incorrecto')
            
            formatted_rut = f"{rut_number}-{dv}"
            return formatted_rut
            
        except ValueError:
            raise
        except Exception:
            raise ValueError('RUT inválido: formato incorrecto')
    
    @field_validator('nombre', 'apellido_paterno', 'apellido_materno')
    @classmethod
    def validate_names(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', v):
            raise ValueError('Solo se permiten letras y espacios')
        return v.strip().title()
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        if v is None:
            return v
        if not re.match(r'^[\+]?[0-9\-\s\(\)]+$', v):
            raise ValueError('Teléfono debe contener solo números y caracteres +, -, espacios, ( )')
        return v
    
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

class UserLoginSchema(BaseModel):
    identifier: str = Field(..., min_length=3, description="RUT o email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
    
    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v):
        v = v.strip()
        if '@' in v:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
                raise ValueError('Email inválido')
            return v.lower()
        else:
            clean_rut = re.sub(r'[.\s-]', '', v)
            
            if len(clean_rut) < 8 or len(clean_rut) > 9:
                raise ValueError('RUT debe tener entre 7 y 8 dígitos más el dígito verificador')
            
            rut_number = clean_rut[:-1]
            dv = clean_rut[-1].upper()
            
            if not rut_number.isdigit() or not re.match(r'^[0-9kK]$', dv):
                raise ValueError('RUT inválido')
            
            return f"{rut_number}-{dv}"

class UserResponseSchema(BaseModel):
    id: int
    nombre: str
    email: str
    rut: str

class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str
    user: UserResponseSchema

class MessageResponseSchema(BaseModel):
    message: str
    user_id: Optional[int] = None

class ResetPasswordSchema(BaseModel):
    token: str = Field(..., min_length=1, description="Token de recuperación")
    nueva_password: str = Field(..., min_length=6, max_length=128, description="Nueva contraseña")
    
    @field_validator('nueva_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('La contraseña debe contener al menos una letra')
        if not re.search(r'[0-9]', v):
            raise ValueError('La contraseña debe contener al menos un número')
        return v

class UserResponseSchema(BaseModel):
    id: int
    nombre: str
    email: str
    rut: str

class PacienteInfoSchema(BaseModel):
    id: int
    nombres: str
    apellidos: str
    rut: str
    email: str
    telefono: Optional[str]
    fecha_nacimiento: Optional[date]

class EspecialidadInfoSchema(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]

class ProfesionalInfoSchema(BaseModel):
    id: int
    nombres: str
    apellidos: str
    especialidad: EspecialidadInfoSchema

class MotivoCancelacionSchema(BaseModel):
    id: int
    descripcion: str

class CitaResponseAdmin(BaseModel):
    id_cita: int
    fecha: date
    hora: time
    estado: str
    observaciones: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    paciente: PacienteInfoSchema
    profesional: ProfesionalInfoSchema
    motivo_cancelacion: Optional[MotivoCancelacionSchema] = None
    
    class Config:
        from_attributes = True
