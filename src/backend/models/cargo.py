from sqlalchemy import Column, SmallInteger, String
from database.connection import Base

class Cargo(Base):
    __tablename__ = "cargo"

    id_cargo = Column(SmallInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(60), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)
