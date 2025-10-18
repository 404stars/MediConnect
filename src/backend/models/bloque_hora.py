from sqlalchemy import Column, BigInteger, Time, Boolean, String, Enum, ForeignKey, UniqueConstraint, CheckConstraint
from database.connection import Base

class BloqueHora(Base):
    __tablename__ = "bloque_hora"

    id_bloque = Column(BigInteger, primary_key=True, autoincrement=True)
    id_agenda = Column(BigInteger, ForeignKey('agenda_diaria.id_agenda'), nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    disponible = Column(Boolean, nullable=False, default=True)
    tipo_bloque = Column(Enum('CONSULTA', 'RESERVADO', 'BLOQUEADO'), nullable=False, default='CONSULTA')
    observaciones = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('id_agenda', 'hora_inicio', name='uk_bloque_agenda_inicio'),
        CheckConstraint('hora_inicio < hora_fin', name='chk_bloque_rango'),
    )
