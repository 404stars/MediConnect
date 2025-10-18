from sqlalchemy import Column, BigInteger, Integer, String, Date, Enum, ForeignKey
from database.connection import Base

class Funcionario(Base):
    __tablename__ = "funcionario"

    id_funcionario = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey('usuario.id_usuario'), nullable=False, unique=True)
    id_cargo = Column(Integer, ForeignKey('cargo.id_cargo'), nullable=True)
    id_comuna = Column(Integer, ForeignKey('comuna.id_comuna'), nullable=True)
    direccion = Column(String(255), nullable=True)
    fecha_contrato = Column(Date, nullable=True)
    estado = Column(Enum('ACTIVO', 'INACTIVO', 'SUSPENDIDO'), nullable=False, default='ACTIVO')
