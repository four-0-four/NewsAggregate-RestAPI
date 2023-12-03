from sqlalchemy import Column, Integer, String
from ..config.database import Base

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(50))
    native = Column(String(50))