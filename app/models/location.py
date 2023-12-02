from sqlalchemy import Column, Integer, String, ForeignKey
from ..config.database import Base

class Continent(Base):
    __tablename__ = "continents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    code = Column(String(5))
    

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    code = Column(String(5))
    capital = Column(String(100))
    phone = Column(Integer)
    native = Column(String(100))
    currency = Column(String(5))
    continent_id = Column(Integer, ForeignKey('continents.id'))
    language_id = Column(Integer, ForeignKey('languages.id'))
    
    
class Province(Base):
    __tablename__ = "provinces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    code = Column(String(5))
    country_id = Column(Integer, ForeignKey('countries.id'))
    

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    province_id = Column(Integer, ForeignKey('provinces.id'))
    country_id = Column(Integer, ForeignKey('countries.id'))