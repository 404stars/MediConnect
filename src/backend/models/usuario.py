from sqlalchemy import Column, BigInteger, String, DateTime, Enum
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(BigInteger, primary_key=True, autoincrement=True)
    rut = Column(String(12), nullable=False, unique=True)
    nombre = Column(String(60), nullable=False)
    apellido_paterno = Column(String(60), nullable=False)
    apellido_materno = Column(String(60), nullable=True)
    email = Column(String(120), nullable=False, unique=True)
    telefono = Column(String(20), nullable=True)
    hash_password = Column(String(255), nullable=False)
    estado = Column(Enum('ACTIVO', 'BLOQUEADO'), nullable=False, default='ACTIVO')
    token_recuperacion = Column(String(255), nullable=True)
    expiracion_token = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("Rol", secondary="usuario_rol", back_populates="usuarios")
