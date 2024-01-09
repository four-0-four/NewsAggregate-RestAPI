from sqlalchemy.orm import Session
from ..models.location import Continent, Country, Province, City
from ..models.news import NewsLocation


def get_continent(db: Session, continent_id: int):
    return db.query(Continent).filter(Continent.id == continent_id).first()


def get_country(db: Session, country_id: int):
    return db.query(Country).filter(Country.id == country_id).first()


def get_province(db: Session, province_id: int):
    return db.query(Province).filter(Province.id == province_id).first()


def get_city(db: Session, city_id: int):
    return db.query(City).filter(City.id == city_id).first()


def find_city_by_name(db, name):
    return db.query(City).filter(City.name == name).first()


def find_province_by_name(db, name):
    return db.query(Province).filter(Province.name == name).first()


def find_country_by_name(db, name):
    return db.query(Country).filter(Country.name == name).first()


def find_continent_by_country(db, country_id):
    country = db.query(Country).filter(Country.id == country_id).first()
    if country:
        return db.query(Continent).filter(Continent.id == country.continent_id).first()
    return None


def add_news_location(db, news_id, continent_id, country_id, province_id, city_id):
    news_location = NewsLocation(
        news_id=news_id,
        continent_id=continent_id,
        country_id=country_id,
        province_id=province_id,
        city_id=city_id
    )
    db.add(news_location)
    db.commit()
