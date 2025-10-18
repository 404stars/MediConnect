import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from typing import Optional, Tuple

from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from models.profesional_salud import ProfesionalSalud
from models.funcionario import Funcionario
from models.usuario import Usuario
from models.especialidad import Especialidad
from models.profesional_especialidad import ProfesionalEspecialidad
from models.paciente import Paciente
from utils.email_utils import enviar_correo_confirmacion, enviar_correo_cancelacion, enviar_correo_reprogramacion

logger = logging.getLogger(__name__)

def obtener_paciente_actual(db: Session, id_usuario: int) -> Paciente:
    paciente = db.query(Paciente).filter(
        Paciente.id_usuario == id_usuario
    ).first()
    
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )
    
    return paciente

def normalizar_rut(rut: str) -> str:
    return rut.replace(".", "").replace("-", "").replace(" ", "").upper() if rut else ""

def buscar_pacientes_por_rut(db: Session, rut_busqueda: str) -> list:
    rut_normalizado = normalizar_rut(rut_busqueda)
    logger.debug(f"Buscando pacientes con RUT: {rut_normalizado}")
    
    todos_pacientes = db.query(Paciente.id_paciente, Usuario.rut).join(Usuario).all()
    
    ids_pacientes_filtrados = []
    for paciente_id, rut_db in todos_pacientes:
        if normalizar_rut(rut_db).find(rut_normalizado) != -1:
            ids_pacientes_filtrados.append(paciente_id)
            logger.debug(f"Match encontrado: Paciente ID={paciente_id}")
    
    logger.debug(f"Total pacientes encontrados: {len(ids_pacientes_filtrados)}")
    return ids_pacientes_filtrados

def obtener_info_bloque_agenda(db: Session, id_bloque: int) -> Tuple[BloqueHora, AgendaDiaria]:
    bloque = db.query(BloqueHora).filter(BloqueHora.id_bloque == id_bloque).first()
    if not bloque:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bloque de hora no encontrado"
        )
    
    agenda = db.query(AgendaDiaria).filter(AgendaDiaria.id_agenda == bloque.id_agenda).first()
    if not agenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda no encontrada"
        )
    
    return bloque, agenda

def obtener_nombre_profesional(db: Session, id_profesional: int) -> str:
    profesional_salud = db.query(ProfesionalSalud).filter(
        ProfesionalSalud.id_profesional == id_profesional
    ).first()
    
    if not profesional_salud:
        return "Profesional de Salud"
    
    funcionario = db.query(Funcionario).filter(
        Funcionario.id_funcionario == profesional_salud.id_funcionario
    ).first()
    
    if not funcionario:
        return "Profesional de Salud"
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == funcionario.id_usuario).first()
    
    if not usuario:
        return "Profesional de Salud"
    
    return f"{usuario.nombre} {usuario.apellido_paterno}"

def obtener_especialidad_profesional(db: Session, id_profesional: int) -> str:
    profesional_especialidad = db.query(ProfesionalEspecialidad).filter(
        ProfesionalEspecialidad.id_profesional == id_profesional
    ).first()
    
    if not profesional_especialidad:
        return "Medicina General"
    
    especialidad = db.query(Especialidad).filter(
        Especialidad.id_especialidad == profesional_especialidad.id_especialidad
    ).first()
    
    return especialidad.nombre if especialidad else "Medicina General"

def validar_tiempo_anticipacion(fecha: datetime, hora, minutos: int = 30):
    fecha_hora = datetime.combine(fecha, hora)
    ahora = datetime.now()
    tiempo_minimo = timedelta(minutes=minutos)
    
    if fecha_hora <= ahora + tiempo_minimo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pueden realizar operaciones con menos de {minutos} minutos de anticipación"
        )

def validar_fecha_pasada(fecha: datetime, hora):
    fecha_hora = datetime.combine(fecha, hora)
    ahora = datetime.now()
    
    if fecha_hora <= ahora:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden realizar operaciones en fechas/horas pasadas"
        )

async def enviar_correo_seguro(func_correo, **kwargs):
    try:
        await func_correo(**kwargs)
    except Exception as e:
        logger.error(f"Error enviando correo: {str(e)}")

def normalizar_rut(rut: str) -> str:
    return rut.replace(".", "").replace("-", "").replace(" ", "").upper()

def buscar_pacientes_por_rut(db: Session, rut_busqueda: str):
    from models.paciente import Paciente
    
    rut_normalizado = normalizar_rut(rut_busqueda)
    logger.info(f"Buscando pacientes con RUT: {rut_normalizado}")
    
    todos_pacientes = db.query(Paciente.id_paciente, Usuario.rut).join(Usuario).all()
    
    ids_pacientes_filtrados = []
    for paciente_id, rut_db in todos_pacientes:
        rut_db_normalizado = normalizar_rut(rut_db) if rut_db else ""
        if rut_normalizado in rut_db_normalizado:
            ids_pacientes_filtrados.append(paciente_id)
            logger.debug(f"Match encontrado: ID={paciente_id}, RUT={rut_db}")
    
    logger.info(f"Total pacientes encontrados: {len(ids_pacientes_filtrados)}")
    return ids_pacientes_filtrados

def obtener_paciente_actual(db: Session, id_usuario: int):
    from models.paciente import Paciente
    
    paciente = db.query(Paciente).filter(
        Paciente.id_usuario == id_usuario
    ).first()
    
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de paciente no encontrado"
        )
    
    return paciente

def obtener_profesional_desde_usuario(db: Session, id_usuario: int) -> Optional[int]:
    funcionario = db.query(Funcionario).filter(
        Funcionario.id_usuario == id_usuario
    ).first()
    
    if not funcionario:
        return None
    
    profesional = db.query(ProfesionalSalud).filter(
        ProfesionalSalud.id_funcionario == funcionario.id_funcionario
    ).first()
    
    return profesional.id_profesional if profesional else None

def validar_cita_duplicada(db: Session, id_paciente: int, id_profesional: int, fecha, hora, excluir_id_cita: Optional[int] = None):
    from models.cita import Cita
    
    query = db.query(Cita).join(
        BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
    ).join(
        AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
    ).filter(
        Cita.id_paciente == id_paciente,
        AgendaDiaria.id_profesional == id_profesional,
        Cita.estado.in_(['AGENDADA', 'CONFIRMADA']),
        AgendaDiaria.fecha == fecha,
        BloqueHora.hora_inicio == hora
    )
    
    if excluir_id_cita:
        query = query.filter(Cita.id_cita != excluir_id_cita)
    
    return query.first()

def validar_cita_conflicto_horario(db: Session, id_paciente: int, fecha, hora):
    from models.cita import Cita
    
    return db.query(Cita).join(
        BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
    ).join(
        AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
    ).filter(
        Cita.id_paciente == id_paciente,
        Cita.estado.in_(['AGENDADA', 'CONFIRMADA', 'EN_ATENCION']),
        AgendaDiaria.fecha == fecha,
        BloqueHora.hora_inicio == hora
    ).first()

def construir_cita_response_admin(cita, bloque, agenda, paciente, usuario_paciente, profesional_salud, usuario_profesional, especialidad, motivo_cancelacion=None):
    cita_data = {
        "id_cita": cita.id_cita,
        "fecha": agenda.fecha,
        "hora": bloque.hora_inicio,
        "estado": cita.estado,
        "observaciones": cita.observaciones,
        "created_at": cita.fecha_solicitud,
        "updated_at": None,
        "paciente": {
            "id": paciente.id_paciente,
            "nombres": usuario_paciente.nombre,
            "apellidos": f"{usuario_paciente.apellido_paterno} {usuario_paciente.apellido_materno or ''}".strip(),
            "rut": usuario_paciente.rut,
            "email": usuario_paciente.email,
            "telefono": usuario_paciente.telefono,
            "fecha_nacimiento": paciente.fecha_nacimiento
        },
        "profesional": {
            "id": profesional_salud.id_profesional,
            "nombres": usuario_profesional.nombre,
            "apellidos": f"{usuario_profesional.apellido_paterno} {usuario_profesional.apellido_materno or ''}".strip(),
            "especialidad": {
                "id": especialidad.id_especialidad,
                "nombre": especialidad.nombre,
                "descripcion": especialidad.descripcion
            }
        }
    }
    
    if motivo_cancelacion:
        cita_data["motivo_cancelacion"] = {
            "id": motivo_cancelacion.id_motivo,
            "descripcion": motivo_cancelacion.descripcion
        }
    
    return cita_data
