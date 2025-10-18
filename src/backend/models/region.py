from sqlalchemy import Column, Integer, String
from database.connection import Base

class Region(Base):
    __tablename__ = "region"

    id_region = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
