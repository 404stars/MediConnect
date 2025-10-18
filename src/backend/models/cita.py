from sqlalchemy import Column, BigInteger, Integer, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class Cita(Base):
    __tablename__ = "cita"

    id_cita = Column(BigInteger, primary_key=True, autoincrement=True)
    id_paciente = Column(BigInteger, ForeignKey('paciente.id_paciente'), nullable=False)
    id_bloque = Column(BigInteger, ForeignKey('bloque_hora.id_bloque'), nullable=False, unique=True)
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.utcnow)
    estado = Column(Enum('AGENDADA', 'CONFIRMADA', 'EN_ATENCION', 'ATENDIDA', 'CANCELADA', 'NO_ASISTIO'), nullable=False, default='AGENDADA')
    motivo_consulta = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    id_motivo_cancelacion = Column(Integer, ForeignKey('motivo_cancelacion.id_motivo'), nullable=True)
    fecha_cancelacion = Column(DateTime, nullable=True)
    cancelada_por = Column(BigInteger, ForeignKey('usuario.id_usuario'), nullable=True)

    paciente = relationship("Paciente", backref="citas")
