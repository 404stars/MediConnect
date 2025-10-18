from sqlalchemy import Column, Integer, String, ForeignKey
from database.connection import Base

class Comuna(Base):
    __tablename__ = "comuna"

    id_comuna = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(80), nullable=False)
    id_region = Column(Integer, ForeignKey('region.id_region'), nullable=False)
