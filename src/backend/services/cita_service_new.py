import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.cita import Cita
from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from models.paciente import Paciente
from models.usuario import Usuario
from validators.cita_validator import CitaValidator
from utils.constants import EstadoCita
from utils.email_utils import enviar_correo_confirmacion
from services.query_service import get_usuario_nombre_completo

logger = logging.getLogger(__name__)


class CitaService:
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_info_bloque_agenda(self, id_bloque: int):
        bloque = self.db.query(BloqueHora).filter(
            BloqueHora.id_bloque == id_bloque
        ).first()
        
        if not bloque:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloque de hora no encontrado"
            )
        
        agenda = self.db.query(AgendaDiaria).filter(
            AgendaDiaria.id_agenda == bloque.id_agenda
        ).first()
        
        if not agenda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agenda no encontrada"
            )
        
        return bloque, agenda
    
    def obtener_nombre_profesional(self, id_profesional: int) -> str:
        from models.profesional_salud import ProfesionalSalud
        from models.funcionario import Funcionario
        
        profesional = self.db.query(ProfesionalSalud).filter(
            ProfesionalSalud.id_profesional == id_profesional
        ).first()
        
        if not profesional:
            return "Profesional no encontrado"
        
        funcionario = self.db.query(Funcionario).filter(
            Funcionario.id_funcionario == profesional.id_funcionario
        ).first()
        
        if not funcionario:
            return "Funcionario no encontrado"
        
        usuario = self.db.query(Usuario).filter(
            Usuario.id_usuario == funcionario.id_usuario
        ).first()
        
        if not usuario:
            return "Usuario no encontrado"
        
        return get_usuario_nombre_completo(usuario)
    
    def obtener_especialidad_profesional(self, id_profesional: int) -> str:
        from models.profesional_especialidad import ProfesionalEspecialidad
        from models.especialidad import Especialidad
        
        especialidad = self.db.query(Especialidad).join(
            ProfesionalEspecialidad
        ).filter(
            ProfesionalEspecialidad.id_profesional == id_profesional
        ).first()
        
        return especialidad.nombre if especialidad else "General"
    
    def validar_disponibilidad_bloque(self, id_bloque: int):
        bloque = self.db.query(BloqueHora).join(AgendaDiaria).filter(
            BloqueHora.id_bloque == id_bloque,
            AgendaDiaria.activa == True
        ).with_for_update().first()
        
        CitaValidator.validar_bloque_disponible(bloque)
        CitaValidator.validar_bloque_no_ocupado(self.db, id_bloque)
        
        return bloque
    
    def validar_limites_paciente(self, id_paciente: int, id_profesional: int, fecha, hora, id_cita_excluir: int = None):
        CitaValidator.validar_cita_duplicada(
            self.db, id_paciente, id_profesional, fecha, hora, id_cita_excluir
        )
        CitaValidator.validar_limite_citas_diarias(self.db, id_paciente, fecha)
    
    def crear_cita(self, id_paciente: int, id_bloque: int, motivo_consulta: str) -> Cita:
        nueva_cita = Cita(
            id_paciente=id_paciente,
            id_bloque=id_bloque,
            fecha_solicitud=datetime.utcnow(),
            estado=EstadoCita.AGENDADA,
            motivo_consulta=motivo_consulta
        )
        
        self.db.add(nueva_cita)
        return nueva_cita
    
    def marcar_bloque_ocupado(self, id_bloque: int):
        bloque = self.db.query(BloqueHora).filter(
            BloqueHora.id_bloque == id_bloque
        ).first()
        
        if bloque:
            bloque.disponible = False
    
    def marcar_bloque_disponible(self, id_bloque: int):
        bloque = self.db.query(BloqueHora).filter(
            BloqueHora.id_bloque == id_bloque
        ).first()
        
        if bloque:
            bloque.disponible = True
    
    async def crear_cita_completa(
        self,
        id_paciente: int,
        id_bloque: int,
        motivo_consulta: str,
        email_paciente: str,
        nombre_paciente: str
    ):
        try:
            bloque = self.validar_disponibilidad_bloque(id_bloque)
            agenda = self.db.query(AgendaDiaria).filter(
                AgendaDiaria.id_agenda == bloque.id_agenda
            ).first()
            
            CitaValidator.validar_tiempo_anticipacion(agenda.fecha, bloque.hora_inicio)
            self.validar_limites_paciente(id_paciente, agenda.id_profesional, agenda.fecha, bloque.hora_inicio)
            
            nueva_cita = self.crear_cita(id_paciente, id_bloque, motivo_consulta)
            self.marcar_bloque_ocupado(id_bloque)
            
            try:
                self.db.commit()
                self.db.refresh(nueva_cita)
            except Exception as e:
                self.db.rollback()
                if "Duplicate entry" in str(e) or "IntegrityError" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Este bloque de hora ya fue tomado por otro usuario. Por favor selecciona otro horario."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error al procesar la solicitud: {str(e)}"
                    )
            
            nombre_profesional = self.obtener_nombre_profesional(agenda.id_profesional)
            especialidad_nombre = self.obtener_especialidad_profesional(agenda.id_profesional)
            
            if email_paciente:
                try:
                    await enviar_correo_confirmacion(
                        email=email_paciente,
                        nombre=nombre_paciente,
                        fecha=agenda.fecha,
                        hora=bloque.hora_inicio,
                        profesional=nombre_profesional,
                        especialidad=especialidad_nombre
                    )
                except Exception as e:
                    logger.warning(f"No se pudo enviar correo de confirmación: {str(e)}")
            
            return {
                "message": "Cita agendada exitosamente",
                "id_cita": nueva_cita.id_cita,
                "fecha": agenda.fecha,
                "hora": bloque.hora_inicio,
                "profesional": nombre_profesional,
                "especialidad": especialidad_nombre
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al agendar la cita: {str(e)}"
            )
    
    def cancelar_cita(
        self,
        id_cita: int,
        id_paciente: int,
        id_motivo_cancelacion: int,
        cancelada_por: int,
        observaciones: Optional[str] = None
    ):
        cita = self.db.query(Cita).filter(
            Cita.id_cita == id_cita,
            Cita.id_paciente == id_paciente,
            Cita.estado.in_(EstadoCita.CANCELABLES)
        ).first()
        
        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada o no se puede cancelar"
            )
        
        bloque, agenda = self.obtener_info_bloque_agenda(cita.id_bloque)
        
        CitaValidator.validar_tiempo_anticipacion(agenda.fecha, bloque.hora_inicio)
        
        cita.estado = EstadoCita.CANCELADA
        cita.id_motivo_cancelacion = id_motivo_cancelacion
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = cancelada_por
        cita.observaciones = observaciones
        
        self.marcar_bloque_disponible(cita.id_bloque)
        
        self.db.commit()
        
        return cita, agenda, bloque
