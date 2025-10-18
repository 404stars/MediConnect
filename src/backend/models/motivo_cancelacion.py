from sqlalchemy import Column, Integer, String, Boolean
from database.connection import Base

class MotivoCancelacion(Base):
    __tablename__ = "motivo_cancelacion"

    id_motivo = Column(Integer, primary_key=True, autoincrement=True)
    descripcion = Column(String(200), nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True)
