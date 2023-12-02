from sqlalchemy.orm import Session
from ..models.location import Continent, Country, Province, City

def get_continent(db: Session, continent_id: int):
    return db.query(Continent).filter(Continent.id == continent_id).first()

def get_country(db: Session, country_id: int):
    return db.query(Country).filter(Country.id == country_id).first()

def get_province(db: Session, province_id: int):
    return db.query(Province).filter(Province.id == province_id).first()

def get_city(db: Session, city_id: int):
    return db.query(City).filter(City.id == city_id).first()