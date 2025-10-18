from sqlalchemy import Column, BigInteger, SmallInteger, Date, ForeignKey
from database.connection import Base

class ProfesionalEspecialidad(Base):
    __tablename__ = "profesional_especialidad"

    id_profesional = Column(BigInteger, ForeignKey('profesional_salud.id_profesional'), primary_key=True)
    id_especialidad = Column(SmallInteger, ForeignKey('especialidad.id_especialidad'), primary_key=True)
    fecha_certificacion = Column(Date, nullable=True)
