from sqlalchemy import Column, SmallInteger, String
from database.connection import Base

class Especialidad(Base):
    __tablename__ = "especialidad"

    id_especialidad = Column(SmallInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(80), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)
