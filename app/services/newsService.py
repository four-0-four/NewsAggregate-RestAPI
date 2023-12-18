from app.models.writer import Writer
from sqlalchemy.orm import Session
from app.models.news import (
    NewsLocation,
    NewsCategory,
    NewsKeywords,
    NewsAffiliates,
    NewsMedia,
)
from fastapi import APIRouter, Depends, Request, UploadFile
from typing import List
from fastapi import HTTPException
from app.models.news import News, NewsInput


#################################### News ####################################
async def add_news_db(db: Session, news_input: NewsInput):
    # Create a new News instance from the NewsInput data
    news = News(
        title=news_input.title,
        description=news_input.description,
        content=news_input.content,
        publishedDate=news_input.publishedDate,
        language_id=news_input.language_id,
        isInternal=news_input.isInternal,
        isPublished=news_input.isPublished
    )

    # Add the news instance to the session
    db.add(news)
    db.commit()
    db.refresh(news)
    return news


async def get_news_by_title(db: Session, title: str):
    return db.query(News).filter(News.title == title).first()


# delete news by id
async def delete_news_by_id(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        db.delete(news)
        db.commit()
        return True
    return False


############################## NewsLocation ##############################
def get_news_location(
        db: Session,
        news_id: int,
        continent_id: int,
        country_id: int,
        province_id: int,
        city_id: int,
):
    return (
        db.query(NewsLocation)
        .filter(
            NewsLocation.news_id == news_id,
            NewsLocation.continent_id == continent_id,
            NewsLocation.country_id == country_id,
            NewsLocation.province_id == province_id,
            NewsLocation.city_id == city_id,
        )
        .first()
    )


def create_news_location(db: Session, location: NewsLocation):
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def delete_news_location(
        db: Session,
        news_id: int,
        continent_id: int,
        country_id: int,
        province_id: int,
        city_id: int,
):
    location = get_news_location(
        db, news_id, continent_id, country_id, province_id, city_id
    )
    if location:
        db.delete(location)
        db.commit()


def update_news_location(
        db: Session,
        news_id: int,
        continent_id: int,
        country_id: int,
        province_id: int,
        city_id: int,
        location: NewsLocation,
):
    db_location = get_news_location(
        db, news_id, continent_id, country_id, province_id, city_id
    )
    if db_location:
        for key, value in location.__dict__.items():
            if key in [
                "news_id",
                "continent_id",
                "country_id",
                "province_id",
                "city_id",
            ]:
                continue
            setattr(db_location, key, value)
        db.commit()
        db.refresh(db_location)
    return db_location


############################### NewsCategory ###############################
def get_news_category(db: Session, news_id: int):
    return db.query(NewsCategory).filter(NewsCategory.news_id == news_id).first()


def create_news_category(db: Session, category: NewsCategory):
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def delete_news_category(db: Session, news_id: int):
    category = get_news_category(db, news_id)
    db.delete(category)
    db.commit()


def update_news_category(db: Session, news_id: int, category: NewsCategory):
    db_category = get_news_category(db, news_id)
    db_category.update(category)
    db.commit()
    db.refresh(db_category)
    return db_category


#################################### NewsKeywords ####################################

def create_news_keyword(db: Session, news_id: int, keyword_id: int):
    news_keyword = get_news_keyword(db, news_id, keyword_id)
    if not news_keyword:
        news_keyword = NewsKeywords(news_id=news_id, keyword_id=keyword_id)
        db.add(news_keyword)
        db.commit()
        db.refresh(news_keyword)
        return news_keyword
    return news_keyword


def get_news_keyword(db: Session, news_id: int, keyword_id: int):
    return (
        db.query(NewsKeywords)
        .filter(NewsKeywords.news_id == news_id, NewsKeywords.keyword_id == keyword_id)
        .first()
    )


def get_all_news_keywords(db: Session, news_id: int):
    return db.query(NewsKeywords).filter(NewsKeywords.news_id == news_id).first()


def delete_news_keyword(db: Session, news_id: int):
    keyword = get_all_news_keywords(db, news_id)
    db.delete(keyword)
    db.commit()


def update_news_keyword(db: Session, news_id: int, keyword: NewsKeywords):
    db_keyword = get_all_news_keywords(db, news_id)
    db_keyword.update(keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


################################### NewsAffiliates ###################################
def get_news_affiliate(
        db: Session, news_id: int, newsCorporation_id: int, externalLink: str
):
    return (
        db.query(NewsAffiliates)
        .filter(
            NewsAffiliates.news_id == news_id,
            NewsAffiliates.newsCorporation_id == newsCorporation_id,
            NewsAffiliates.externalLink == externalLink,
        )
        .first()
    )


def create_news_affiliate(db: Session, affiliate: NewsAffiliates):
    db.add(affiliate)
    db.commit()
    db.refresh(affiliate)
    return affiliate


def delete_news_affiliate(
        db: Session, news_id: int, newsCorporation_id: int, externalLink: str
):
    affiliate = get_news_affiliate(db, news_id, newsCorporation_id, externalLink)
    if affiliate:
        db.delete(affiliate)
        db.commit()


def update_news_affiliate(
        db: Session,
        news_id: int,
        newsCorporation_id: int,
        externalLink: str,
        affiliate: NewsAffiliates,
):
    db_affiliate = get_news_affiliate(db, news_id, newsCorporation_id, externalLink)
    if db_affiliate:
        for key, value in affiliate.__dict__.items():
            if key in ["news_id", "newsCorporation_id", "externalLink"]:
                continue
            setattr(db_affiliate, key, value)
        db.commit()
        db.refresh(db_affiliate)
    return db_affiliate


################################### NewsMedia ###################################
def get_news_media(db: Session, news_id: int, media_id: int):
    return (
        db.query(NewsMedia)
        .filter(NewsMedia.news_id == news_id, NewsMedia.media_id == media_id)
        .first()
    )


def create_news_media(db: Session, media: NewsMedia):
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def delete_news_media(db: Session, news_id: int, media_id: int):
    media = get_news_media(db, news_id, media_id)
    if media:
        db.delete(media)
        db.commit()


def update_news_media(db: Session, news_id: int, media_id: int, media: NewsMedia):
    db_media = get_news_media(db, news_id, media_id)
    if db_media:
        for key, value in media.__dict__.items():
            if key in ["news_id", "media_id"]:
                continue
            setattr(db_media, key, value)
        db.commit()
        db.refresh(db_media)
    return db_media
