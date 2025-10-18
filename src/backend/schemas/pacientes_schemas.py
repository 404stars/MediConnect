from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

class EspecialidadResponse(BaseModel):
    id_especialidad: int
    nombre: str
    descripcion: Optional[str] = None

class MotivoCancelacionResponse(BaseModel):
    id_motivo: int
    descripcion: str

class ProfesionalResponse(BaseModel):
    id_profesional: int
    nombre_completo: str
    registro_profesional: str
    especialidades: List[str]

class BloqueDisponibleResponse(BaseModel):
    id_bloque: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    profesional: str
    especialidad: str

class CitaResponse(BaseModel):
    id_cita: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    estado: str
    profesional: str
    especialidad: str
    motivo_consulta: Optional[str]
    observaciones: Optional[str]

class SolicitarCitaRequest(BaseModel):
    id_bloque: int
    motivo_consulta: Optional[str] = None

class CancelarCitaRequest(BaseModel):
    id_motivo_cancelacion: int
    observaciones: Optional[str] = None

class ReprogramarCitaRequest(BaseModel):
    id_nuevo_bloque: int
    id_motivo_cancelacion: int
    observaciones: Optional[str] = None
