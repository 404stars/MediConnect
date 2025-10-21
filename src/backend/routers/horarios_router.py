import logging
from datetime import date, time, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from pydantic import BaseModel, field_validator

from database.connection import get_db
from models import (
    Usuario, ProfesionalSalud, Funcionario, AgendaDiaria,
    BloqueHora, Especialidad, ProfesionalEspecialidad,
    UsuarioRol, Rol, Cita
)
from utils import (
    get_current_user, require_roles, require_any_role,
    has_any_role, Rol as RolConstantes
)
from services import get_usuario_nombre_completo, AgendaService
from validators import HorarioValidator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/horarios", tags=["Gestión de Horarios"])
security = HTTPBearer()


class EspecialidadResponse(BaseModel):
    id_especialidad: int
    nombre: str
    descripcion: Optional[str] = None
    
    class Config:
        from_attributes = True

class MedicoResponse(BaseModel):
    id_profesional: int
    id_usuario: int
    nombre_completo: str
    rut: str
    registro_profesional: str
    especialidades: List[EspecialidadResponse] = []
    
    class Config:
        from_attributes = True

class BloqueHoraRequest(BaseModel):
    inicio: time
    fin: time
    
    @field_validator('fin')
    @classmethod
    def validar_rango_tiempo(cls, v, values):
        if 'inicio' in values.data and v <= values.data['inicio']:
            raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v

class AgendaDiariaRequest(BaseModel):
    id_profesional: int
    fecha: date
    hora_inicio: time
    hora_fin: time
    duracion_cita: int = 30
    observaciones: Optional[str] = None
    bloques: Optional[List[BloqueHoraRequest]] = []
    
    @field_validator('hora_fin')
    @classmethod
    def validar_horarios(cls, v, values):
        if 'hora_inicio' in values.data and values.data.get('hora_inicio'):
            if v <= values.data['hora_inicio']:
                raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v
    
    @field_validator('duracion_cita')
    @classmethod
    def validar_duracion(cls, v):
        if v < 15:
            raise ValueError('La duración mínima de cita es de 15 minutos')
        if v > 240:
            raise ValueError('La duración máxima de cita es de 4 horas (240 minutos)')
        return v
    
    @field_validator('bloques')
    @classmethod
    def validar_bloques(cls, v):
        if not v:
            return v
        
        bloques_ordenados = sorted(v, key=lambda x: x.inicio)
        for i in range(len(bloques_ordenados) - 1):
            if bloques_ordenados[i].fin > bloques_ordenados[i + 1].inicio:
                raise ValueError(f'Los bloques horarios se solapan: {bloques_ordenados[i].fin} - {bloques_ordenados[i + 1].inicio}')
        
        return v

class AsignarEspecialidadRequest(BaseModel):
    id_profesional: int
    id_especialidad: int
    fecha_certificacion: Optional[date] = None

def generar_bloques_automaticos(hora_inicio: time, hora_fin: time, duracion_cita: int) -> List[dict]:
    bloques = []
    
    inicio = datetime.combine(date.today(), hora_inicio)
    fin = datetime.combine(date.today(), hora_fin)
    
    if inicio >= fin:
        return bloques
    
    tiempo_total = (fin - inicio).total_seconds() / 60
    if tiempo_total < duracion_cita:
        return bloques
    
    actual = inicio
    while actual + timedelta(minutes=duracion_cita) <= fin:
        siguiente = actual + timedelta(minutes=duracion_cita)
        bloques.append({
            "hora_inicio": actual.time(),
            "hora_fin": siguiente.time()
        })
        actual = siguiente
    
    return bloques

@router.get("/medicos", response_model=List[MedicoResponse])
async def listar_medicos(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_roles([RolConstantes.ADMINISTRADOR, RolConstantes.RECEPCIONISTA]))
):
    """
    Optimizado: Usa joinedload para eliminar N+1 queries.
    Antes: 1 + 3N queries (N = número de médicos)
    Después: 1 query única con JOINs
    """
    try:
        medicos = db.query(ProfesionalSalud).options(
            joinedload(ProfesionalSalud.funcionario).joinedload(Funcionario.usuario),
            joinedload(ProfesionalSalud.profesional_especialidades).joinedload(ProfesionalEspecialidad.especialidad)
        ).join(
            Funcionario, ProfesionalSalud.id_funcionario == Funcionario.id_funcionario
        ).join(
            Usuario, Funcionario.id_usuario == Usuario.id_usuario
        ).join(
            UsuarioRol, Usuario.id_usuario == UsuarioRol.id_usuario
        ).join(
            Rol, UsuarioRol.id_rol == Rol.id_rol
        ).filter(
            Rol.nombre == RolConstantes.MEDICO,
            Usuario.estado == "ACTIVO"
        ).all()
        
        resultado = []
        for medico in medicos:
            usuario = medico.funcionario.usuario
            
            especialidades = [
                {
                    "id_especialidad": esp_rel.especialidad.id_especialidad,
                    "nombre": esp_rel.especialidad.nombre,
                    "descripcion": esp_rel.especialidad.descripcion,
                    "es_principal": False
                }
                for esp_rel in medico.profesional_especialidades
            ]
            
            resultado.append(MedicoResponse(
                id_profesional=medico.id_profesional,
                id_usuario=usuario.id_usuario,
                nombre_completo=get_usuario_nombre_completo(usuario),
                rut=usuario.rut,
                registro_profesional=medico.registro_profesional,
                especialidades=especialidades
            ))
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en consulta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

@router.post("/asignar-especialidad")
async def asignar_especialidad(
    request: AsignarEspecialidadRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_roles([RolConstantes.ADMINISTRADOR]))
):
    
    profesional = db.query(ProfesionalSalud).filter(
        ProfesionalSalud.id_profesional == request.id_profesional
    ).first()
    
    if not profesional:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profesional no encontrado"
        )
    
    especialidad = db.query(Especialidad).filter(
        Especialidad.id_especialidad == request.id_especialidad
    ).first()
    
    if not especialidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Especialidad no encontrada"
        )
    
    asignacion_existente = db.query(ProfesionalEspecialidad).filter(
        and_(
            ProfesionalEspecialidad.id_profesional == request.id_profesional,
            ProfesionalEspecialidad.id_especialidad == request.id_especialidad
        )
    ).first()
    
    if asignacion_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La especialidad ya está asignada a este profesional"
        )
    
    nueva_asignacion = ProfesionalEspecialidad(
        id_profesional=request.id_profesional,
        id_especialidad=request.id_especialidad,
        fecha_certificacion=request.fecha_certificacion or date.today()
    )
    
    db.add(nueva_asignacion)
    db.commit()
    
    return {"message": "Especialidad asignada exitosamente"}

@router.delete("/especialidad/{id_profesional}/{id_especialidad}")
async def quitar_especialidad(
    id_profesional: int,
    id_especialidad: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_roles([RolConstantes.ADMINISTRADOR]))
):
    
    asignacion = db.query(ProfesionalEspecialidad).filter(
        and_(
            ProfesionalEspecialidad.id_profesional == id_profesional,
            ProfesionalEspecialidad.id_especialidad == id_especialidad
        )
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación de especialidad no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    
    return {"message": "Especialidad removida exitosamente"}

@router.post("/agenda")
async def crear_agenda_diaria(
    request: AgendaDiariaRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_roles([RolConstantes.ADMINISTRADOR, RolConstantes.RECEPCIONISTA]))
):
    agenda_service = AgendaService(db)
    
    bloques_formateados = None
    if request.bloques:
        bloques_formateados = [{"inicio": b.inicio, "fin": b.fin} for b in request.bloques]
    
    return agenda_service.crear_agenda_completa(
        id_profesional=request.id_profesional,
        fecha=request.fecha,
        hora_inicio=request.hora_inicio,
        hora_fin=request.hora_fin,
        duracion_cita=request.duracion_cita,
        bloques=bloques_formateados,
        observaciones=request.observaciones
    )

@router.get("/agendas")
async def obtener_todas_las_agendas(
    id_profesional: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    _: int = Depends(require_any_role([RolConstantes.ADMINISTRADOR, RolConstantes.RECEPCIONISTA, RolConstantes.MEDICO]))
):
    """
    Optimizado: Usa decorador para validación de roles en lugar de validaciones manuales
    """
    # Si es médico (y no admin/recepcionista), solo puede ver su propia agenda
    if has_any_role(current_user.id_usuario, [RolConstantes.MEDICO], db) and \
       not has_any_role(current_user.id_usuario, [RolConstantes.ADMINISTRADOR, RolConstantes.RECEPCIONISTA], db):
        funcionario = db.query(Funcionario).filter(Funcionario.id_usuario == current_user.id_usuario).first()
        if funcionario:
            profesional_actual = db.query(ProfesionalSalud).filter(
                ProfesionalSalud.id_funcionario == funcionario.id_funcionario
            ).first()
            if profesional_actual:
                id_profesional = profesional_actual.id_profesional
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No se encontró perfil de profesional"
                )
    
    query = db.query(AgendaDiaria)
    
    if id_profesional:
        query = query.filter(AgendaDiaria.id_profesional == id_profesional)
    
    if fecha_inicio:
        query = query.filter(AgendaDiaria.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(AgendaDiaria.fecha <= fecha_fin)
    
    agendas = query.order_by(AgendaDiaria.fecha).all()
    
    resultado = []
    for agenda in agendas:
        profesional = db.query(ProfesionalSalud).filter(
            ProfesionalSalud.id_profesional == agenda.id_profesional
        ).first()
        
        if profesional:
            funcionario = db.query(Funcionario).filter(
                Funcionario.id_funcionario == profesional.id_funcionario
            ).first()
            
            if funcionario:
                usuario = db.query(Usuario).filter(
                    Usuario.id_usuario == funcionario.id_usuario
                ).first()
                
                nombre_medico = get_usuario_nombre_completo(usuario) if usuario else "N/A"
            else:
                nombre_medico = "N/A"
        else:
            nombre_medico = "N/A"
        
        bloques = db.query(BloqueHora).filter(
            BloqueHora.id_agenda == agenda.id_agenda
        ).order_by(BloqueHora.hora_inicio).all()
        
        resultado.append({
            "id_agenda": agenda.id_agenda,
            "id_profesional": agenda.id_profesional,
            "nombre_medico": nombre_medico,
            "fecha": agenda.fecha,
            "hora_inicio": agenda.hora_inicio,
            "hora_fin": agenda.hora_fin,
            "duracion_cita": agenda.duracion_cita,
            "activa": agenda.activa,
            "observaciones": agenda.observaciones,
            "bloques": [{
                "id_bloque": bloque.id_bloque,
                "inicio": bloque.hora_inicio,
                "fin": bloque.hora_fin,
                "disponible": bloque.disponible,
                "tipo_bloque": bloque.tipo_bloque,
                "observaciones": bloque.observaciones
            } for bloque in bloques]
        })
    
    return resultado

@router.delete("/agenda/{id_agenda}")
async def eliminar_agenda(
    id_agenda: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(require_roles([RolConstantes.ADMINISTRADOR, RolConstantes.RECEPCIONISTA]))
):
    
    agenda = db.query(AgendaDiaria).filter(AgendaDiaria.id_agenda == id_agenda).first()
    
    if not agenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda no encontrada"
        )
    
    citas_activas = db.query(Cita).join(BloqueHora).filter(
        BloqueHora.id_agenda == id_agenda,
        Cita.estado.in_(['AGENDADA', 'CONFIRMADA', 'EN_ATENCION'])
    ).count()
    
    if citas_activas > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la agenda porque tiene citas reservadas o confirmadas"
        )
    
    db.query(BloqueHora).filter(BloqueHora.id_agenda == id_agenda).delete()
    
    db.delete(agenda)
    db.commit()
    
    return {"message": "Agenda eliminada exitosamente"}
