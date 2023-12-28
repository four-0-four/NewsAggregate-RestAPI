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
def add_news_db(db: Session, news_input: NewsInput):
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


def get_news_by_title(db: Session, title: str):
    return db.query(News).filter(News.title == title).first()


# delete news by id
def delete_news_by_title(db: Session, news_title: str):
    # Find the news item by title
    news = db.query(News).filter(News.title == news_title).first()

    if news:
        # Delete associated NewsCategories
        db.query(NewsCategory).filter(NewsCategory.news_id == news.id).delete()

        # Delete associated NewsKeywords
        db.query(NewsKeywords).filter(NewsKeywords.news_id == news.id).delete()

        # Delete associated NewsMedia
        db.query(NewsMedia).filter(NewsMedia.news_id == news.id).delete()

        # TODO: Delete associated NewsAffiliates

        # Now delete the news item itself
        db.delete(news)
        db.commit()
        return news

    return None


############################### NewsCategory ###############################


def get_news_category(db: Session, news_id: int, category_id: int):
    return db.query(NewsCategory).filter(NewsCategory.news_id == news_id, NewsCategory.category_id == category_id).first()


def create_news_category(db: Session, news_id: int, category_id: int):
    # Check if the news_category already exists
    existing_news_category = get_news_category(db, news_id, category_id)

    # If it exists, return the existing entry
    if existing_news_category:
        return existing_news_category

    # If it does not exist, create a new instance of NewsCategory
    new_news_category = NewsCategory(news_id=news_id, category_id=category_id)

    # Add the new instance to the session and commit
    db.add(new_news_category)
    db.commit()

    # Refresh to get the data from the database, if necessary
    db.refresh(new_news_category)

    return new_news_category



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


def create_news_media(db: Session, news_id: int, media_id: int):
    news_media = get_news_media(db, news_id, media_id)
    if not news_media:
        news_media = NewsMedia(news_id=news_id, media_id=media_id)
        db.add(news_media)
        db.commit()
        db.refresh(news_media)
    return news_media


def get_news_media(db: Session, news_id: int, media_id: int):
    return (
        db.query(NewsMedia)
        .filter(NewsMedia.news_id == news_id, NewsMedia.media_id == media_id)
        .first()
    )
