from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from database.connection import Base

class Rol(Base):
    __tablename__ = "rol"

    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(40), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)
    permisos = Column(Text, nullable=True)

    usuarios = relationship("Usuario", secondary="usuario_rol", back_populates="roles")

    def get_permisos_list(self):
        if self.permisos:
            return [p.strip() for p in self.permisos.split(',')]
        return []
