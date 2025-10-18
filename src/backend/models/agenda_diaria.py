from sqlalchemy import Column, BigInteger, Integer, Date, Time, Boolean, Text, ForeignKey, UniqueConstraint
from database.connection import Base

class AgendaDiaria(Base):
    __tablename__ = "agenda_diaria"

    id_agenda = Column(BigInteger, primary_key=True, autoincrement=True)
    id_profesional = Column(BigInteger, ForeignKey('profesional_salud.id_profesional'), nullable=False)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    duracion_cita = Column(Integer, nullable=False, default=30)
    activa = Column(Boolean, nullable=False, default=True)
    observaciones = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('id_profesional', 'fecha', name='uk_agenda_prof_fecha'),
    )
