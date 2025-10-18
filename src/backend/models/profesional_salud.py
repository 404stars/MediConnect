from sqlalchemy import Column, BigInteger, String, Date, Enum, ForeignKey
from database.connection import Base

class ProfesionalSalud(Base):
    __tablename__ = "profesional_salud"

    id_profesional = Column(BigInteger, primary_key=True, autoincrement=True)
    id_funcionario = Column(BigInteger, ForeignKey('funcionario.id_funcionario'), nullable=False, unique=True)
    registro_profesional = Column(String(50), nullable=False, unique=True)
    fecha_titulo = Column(Date, nullable=True)
    estado_registro = Column(Enum('VIGENTE', 'SUSPENDIDO', 'CADUCADO'), nullable=False, default='VIGENTE')
