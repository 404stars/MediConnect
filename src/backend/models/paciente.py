from sqlalchemy import Column, BigInteger, String, Date, Enum, Integer, ForeignKey, Text
from database.connection import Base
from models.usuario import Usuario
from sqlalchemy.orm import relationship


class Paciente(Base):
    __tablename__ = "paciente"

    id_paciente = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey('usuario.id_usuario'), nullable=False, unique=True)
    fecha_nacimiento = Column(Date, nullable=True)
    sexo = Column(Enum('M', 'F', 'I'), nullable=True)
    id_comuna = Column(Integer, ForeignKey('comuna.id_comuna'), nullable=True)
    direccion = Column(String(255), nullable=True)
    contacto_emergencia = Column(String(100), nullable=True)
    telefono_emergencia = Column(String(20), nullable=True)
    alergias = Column(Text, nullable=True)
    condiciones_medicas = Column(Text, nullable=True)

    usuario = relationship("Usuario", backref="paciente")