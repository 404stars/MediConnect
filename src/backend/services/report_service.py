import csv
import io
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from models.cita import Cita
from models.bloque_hora import BloqueHora
from models.agenda_diaria import AgendaDiaria
from models.motivo_cancelacion import MotivoCancelacion
from services.query_service import get_profesional_info, get_paciente_info

logger = logging.getLogger(__name__)

def generar_csv_citas(citas, db: Session):
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        'ID Cita', 'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado',
        'RUT Paciente', 'Nombre Paciente', 'Email Paciente', 'Telefono Paciente',
        'Profesional', 'Especialidad', 'Observaciones', 'Motivo Cancelacion', 'Fecha Creacion'
    ]
    writer.writerow(headers)

    for cita in citas:
        try:
            bloque = db.query(BloqueHora).filter(BloqueHora.id_bloque == cita.id_bloque).first()
            if not bloque:
                logger.warning(f"No se encontró bloque para cita {cita.id_cita}")
                continue
                
            agenda = db.query(AgendaDiaria).filter(AgendaDiaria.id_agenda == bloque.id_agenda).first()
            if not agenda:
                logger.warning(f"No se encontró agenda para cita {cita.id_cita}")
                continue
            
            fecha_cita = agenda.fecha.strftime('%Y-%m-%d')
            
            _, _, rut_paciente, nombre_paciente, email_paciente, telefono_paciente = get_paciente_info(db, cita.id_paciente)
            
            _, _, nombre_profesional, especialidad_nombre = get_profesional_info(db, agenda.id_profesional)
            
            motivo_cancelacion = ""
            if cita.id_motivo_cancelacion:
                motivo = db.query(MotivoCancelacion).filter(
                    MotivoCancelacion.id_motivo == cita.id_motivo_cancelacion
                ).first()
                if motivo:
                    motivo_cancelacion = motivo.descripcion
            
            row = [
                cita.id_cita,
                fecha_cita,
                bloque.hora_inicio.strftime('%H:%M') if bloque.hora_inicio else 'N/A',
                bloque.hora_fin.strftime('%H:%M') if bloque.hora_fin else 'N/A',
                cita.estado or '',
                rut_paciente,
                nombre_paciente,
                email_paciente,
                telefono_paciente,
                nombre_profesional,
                especialidad_nombre,
                cita.observaciones or '',
                motivo_cancelacion,
                cita.fecha_solicitud.strftime('%Y-%m-%d %H:%M:%S') if cita.fecha_solicitud else ''
            ]
            writer.writerow(row)
            
        except Exception as row_error:
            logger.error(f"Error procesando cita {cita.id_cita}: {str(row_error)}")
            continue
    
    output.seek(0)
    csv_content = output.getvalue()
    output.close()
    
    return csv_content

def generar_csv_pacientes_atendidos(citas, db: Session):
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        'ID Cita', 'Fecha Atención', 'Hora Inicio', 'Hora Fin',
        'RUT Paciente', 'Nombre Paciente', 'Email Paciente', 'Telefono Paciente',
        'Profesional', 'Especialidad', 'Observaciones'
    ]
    writer.writerow(headers)
    
    for cita in citas:
        try:
            bloque = db.query(BloqueHora).filter(BloqueHora.id_bloque == cita.id_bloque).first()
            if not bloque:
                continue
                
            agenda = db.query(AgendaDiaria).filter(AgendaDiaria.id_agenda == bloque.id_agenda).first()
            if not agenda:
                continue

            _, _, rut_paciente, nombre_paciente, email_paciente, telefono_paciente = get_paciente_info(db, cita.id_paciente)
            
            _, _, nombre_profesional, especialidad_nombre = get_profesional_info(db, agenda.id_profesional)

            row = [
                cita.id_cita,
                agenda.fecha.strftime('%Y-%m-%d') if agenda.fecha else 'N/A',
                bloque.hora_inicio.strftime('%H:%M') if bloque.hora_inicio else 'N/A',
                bloque.hora_fin.strftime('%H:%M') if bloque.hora_fin else 'N/A',
                rut_paciente,
                nombre_paciente,
                email_paciente,
                telefono_paciente,
                nombre_profesional,
                especialidad_nombre,
                cita.observaciones or ''
            ]
            writer.writerow(row)
            
        except Exception as row_error:
            logger.error(f"Error procesando cita atendida {cita.id_cita}: {str(row_error)}")
            continue

    output.seek(0)
    csv_content = output.getvalue()
    output.close()
    
    return csv_content
