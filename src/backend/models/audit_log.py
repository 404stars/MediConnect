from sqlalchemy import Column, BigInteger, String, JSON, DateTime, Enum, ForeignKey
from database.connection import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_log"

    id_log = Column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario = Column(BigInteger, ForeignKey('usuario.id_usuario'), nullable=True)
    tabla_afectada = Column(String(50), nullable=False)
    operacion = Column(Enum('INSERT', 'UPDATE', 'DELETE'), nullable=False)
    datos_anteriores = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)
    fecha_operacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
