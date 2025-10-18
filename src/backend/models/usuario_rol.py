from sqlalchemy import Column, BigInteger, SmallInteger, ForeignKey
from database.connection import Base

class UsuarioRol(Base):
    __tablename__ = "usuario_rol"

    id_usuario = Column(BigInteger, ForeignKey('usuario.id_usuario'), primary_key=True)
    id_rol = Column(SmallInteger, ForeignKey('rol.id_rol'), primary_key=True)
