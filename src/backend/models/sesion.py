from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Boolean, Text
from database.connection import Base
from datetime import datetime

class Sesion(Base):
    __tablename__ = "sesion"

    id_sesion = Column(String(100), primary_key=True)
    id_usuario = Column(BigInteger, ForeignKey('usuario.id_usuario'), nullable=False)
    token_jwt = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime, nullable=False)
    activa = Column(Boolean, nullable=False, default=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
