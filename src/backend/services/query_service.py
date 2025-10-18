import logging
from sqlalchemy.orm import Session
from models.usuario import Usuario
from models.profesional_salud import ProfesionalSalud
from models.funcionario import Funcionario
from models.especialidad import Especialidad
from models.profesional_especialidad import ProfesionalEspecialidad
from models.paciente import Paciente

logger = logging.getLogger(__name__)

def get_usuario_nombre_completo(usuario: Usuario) -> str:
    if not usuario:
        return "N/A"
    apellidos = f"{usuario.apellido_paterno} {usuario.apellido_materno or ''}".strip()
    return f"{usuario.nombre} {apellidos}".strip()

def get_profesional_info(db: Session, id_profesional: int):
    profesional = db.query(ProfesionalSalud).filter(
        ProfesionalSalud.id_profesional == id_profesional
    ).first()
    
    if not profesional:
        return None, None, "No especificado", "No especificada"
    
    funcionario = db.query(Funcionario).filter(
        Funcionario.id_funcionario == profesional.id_funcionario
    ).first()
    
    if not funcionario:
        return profesional, None, "No especificado", "No especificada"
    
    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == funcionario.id_usuario
    ).first()
    
    nombre_profesional = get_usuario_nombre_completo(usuario) if usuario else "No especificado"
    
    especialidad_rel = db.query(ProfesionalEspecialidad).filter(
        ProfesionalEspecialidad.id_profesional == profesional.id_profesional
    ).first()
    
    especialidad_nombre = "No especificada"
    if especialidad_rel:
        especialidad = db.query(Especialidad).filter(
            Especialidad.id_especialidad == especialidad_rel.id_especialidad
        ).first()
        if especialidad:
            especialidad_nombre = especialidad.nombre
    
    return profesional, usuario, nombre_profesional, especialidad_nombre

def get_paciente_info(db: Session, id_paciente: int):
    paciente = db.query(Paciente).filter(
        Paciente.id_paciente == id_paciente
    ).first()
    
    if not paciente:
        return None, None, "N/A", "N/A", "N/A", "N/A"
    
    usuario = db.query(Usuario).filter(
        Usuario.id_usuario == paciente.id_usuario
    ).first()
    
    if not usuario:
        return paciente, None, "N/A", "N/A", "N/A", "N/A"
    
    return (
        paciente,
        usuario,
        usuario.rut,
        get_usuario_nombre_completo(usuario),
        usuario.email,
        usuario.telefono or "N/A"
    )
