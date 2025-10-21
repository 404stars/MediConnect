from datetime import datetime, timedelta, date, time
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.cita import Cita
from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from utils.constants import EstadoCita


class CitaValidator:
    ANTICIPACION_MINIMA_HORAS = 2
    MAX_CITAS_POR_DIA = 3
    
    @staticmethod
    def validar_tiempo_anticipacion(fecha: date, hora: time):
        fecha_hora_cita = datetime.combine(fecha, hora)
        tiempo_minimo = datetime.now() + timedelta(hours=CitaValidator.ANTICIPACION_MINIMA_HORAS)
        
        if fecha_hora_cita <= tiempo_minimo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Las citas deben agendarse con al menos {CitaValidator.ANTICIPACION_MINIMA_HORAS} horas de anticipación"
            )
    
    @staticmethod
    def validar_cita_duplicada(db: Session, id_paciente: int, id_profesional: int, 
                               fecha: date, hora: time, excluir_cita_id: int = None):
        query = db.query(Cita).join(
            BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
        ).join(
            AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
        ).filter(
            Cita.id_paciente == id_paciente,
            AgendaDiaria.id_profesional == id_profesional,
            AgendaDiaria.fecha == fecha,
            BloqueHora.hora_inicio == hora,
            Cita.estado.in_(EstadoCita.ACTIVAS)
        )
        
        if excluir_cita_id:
            query = query.filter(Cita.id_cita != excluir_cita_id)
        
        cita_existente = query.first()
        
        if cita_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tienes una cita agendada con este profesional en la misma fecha y hora"
            )
    
    @staticmethod
    def validar_limite_citas_diarias(db: Session, id_paciente: int, fecha: date):
        citas_mismo_dia = db.query(Cita).join(
            BloqueHora, Cita.id_bloque == BloqueHora.id_bloque
        ).join(
            AgendaDiaria, BloqueHora.id_agenda == AgendaDiaria.id_agenda
        ).filter(
            Cita.id_paciente == id_paciente,
            Cita.estado.in_(EstadoCita.CANCELABLES),
            AgendaDiaria.fecha == fecha
        ).count()
        
        if citas_mismo_dia >= CitaValidator.MAX_CITAS_POR_DIA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No puedes tener más de {CitaValidator.MAX_CITAS_POR_DIA} citas agendadas en un mismo día"
            )
    
    @staticmethod
    def validar_bloque_disponible(bloque: BloqueHora):
        if not bloque:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloque de hora no encontrado o agenda inactiva"
            )
        
        if not bloque.disponible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este bloque de hora ya no está disponible"
            )
    
    @staticmethod
    def validar_bloque_no_ocupado(db: Session, id_bloque: int):
        cita_existente = db.query(Cita).filter(
            Cita.id_bloque == id_bloque,
            Cita.estado.in_(EstadoCita.ACTIVAS)
        ).first()
        
        if cita_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este bloque de hora ya está ocupado por otra cita"
            )
