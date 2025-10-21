import logging
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from models.agenda_diaria import AgendaDiaria
from models.bloque_hora import BloqueHora
from models.profesional_salud import ProfesionalSalud
from validators.horario_validator import HorarioValidator

logger = logging.getLogger(__name__)


class AgendaService:
    def __init__(self, db: Session):
        self.db = db
    
    def validar_profesional_existe(self, id_profesional: int):
        profesional = self.db.query(ProfesionalSalud).filter(
            ProfesionalSalud.id_profesional == id_profesional
        ).first()
        
        if not profesional:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profesional no encontrado"
            )
        
        return profesional
    
    def validar_agenda_no_existe(self, id_profesional: int, fecha: date):
        agenda_existente = self.db.query(AgendaDiaria).filter(
            and_(
                AgendaDiaria.id_profesional == id_profesional,
                AgendaDiaria.fecha == fecha
            )
        ).first()
        
        if agenda_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una agenda para este profesional en la fecha especificada"
            )
    
    def generar_bloques_automaticos(
        self,
        hora_inicio: time,
        hora_fin: time,
        duracion_cita: int
    ) -> List[dict]:
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
    
    def crear_agenda(
        self,
        id_profesional: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        duracion_cita: int,
        observaciones: Optional[str] = None
    ) -> AgendaDiaria:
        nueva_agenda = AgendaDiaria(
            id_profesional=id_profesional,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            duracion_cita=duracion_cita,
            activa=True,
            observaciones=observaciones
        )
        
        self.db.add(nueva_agenda)
        self.db.flush()
        
        return nueva_agenda
    
    def crear_bloques_para_agenda(
        self,
        id_agenda: int,
        bloques_data: Optional[List[dict]] = None,
        hora_inicio: Optional[time] = None,
        hora_fin: Optional[time] = None,
        duracion_cita: Optional[int] = None
    ):
        if not bloques_data:
            if not all([hora_inicio, hora_fin, duracion_cita]):
                raise ValueError("Se requiere hora_inicio, hora_fin y duracion_cita para generar bloques automáticos")
            
            bloques_data = self.generar_bloques_automaticos(hora_inicio, hora_fin, duracion_cita)
        
        bloques_creados = []
        for bloque_data in bloques_data:
            nuevo_bloque = BloqueHora(
                id_agenda=id_agenda,
                hora_inicio=bloque_data.get("hora_inicio") or bloque_data.get("inicio"),
                hora_fin=bloque_data.get("hora_fin") or bloque_data.get("fin"),
                disponible=True
            )
            self.db.add(nuevo_bloque)
            bloques_creados.append(nuevo_bloque)
        
        return bloques_creados
    
    def crear_agenda_completa(
        self,
        id_profesional: int,
        fecha: date,
        hora_inicio: time,
        hora_fin: time,
        duracion_cita: int,
        bloques: Optional[List[dict]] = None,
        observaciones: Optional[str] = None
    ):
        try:
            HorarioValidator.validar_horarios_completos(hora_inicio, hora_fin, fecha)
            
            self.validar_profesional_existe(id_profesional)
            self.validar_agenda_no_existe(id_profesional, fecha)
            
            nueva_agenda = self.crear_agenda(
                id_profesional=id_profesional,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                duracion_cita=duracion_cita,
                observaciones=observaciones
            )
            
            bloques_creados = self.crear_bloques_para_agenda(
                id_agenda=nueva_agenda.id_agenda,
                bloques_data=bloques,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                duracion_cita=duracion_cita
            )
            
            self.db.commit()
            
            logger.info(f"Agenda {nueva_agenda.id_agenda} creada con {len(bloques_creados)} bloques")
            
            return {
                "message": "Agenda creada exitosamente",
                "id_agenda": nueva_agenda.id_agenda,
                "bloques_creados": len(bloques_creados)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating agenda: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear la agenda: {str(e)}"
            )
