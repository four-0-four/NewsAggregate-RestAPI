from datetime import timedelta, datetime

from sqlalchemy import func

from app.models.common import Media, Keyword, NewsCorporations
from app.models.user import UserCategoryFollowing, UserKeywordFollowing
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


def get_news_by_category(db: Session, category_id: int, hours: int = 0):
    if hours == 0 or hours is None:
        return (
            db.query(News)
            .join(NewsCategory)
            .filter(NewsCategory.category_id == category_id)
            .all()
        )

    twelve_hours_ago = datetime.utcnow() - timedelta(hours=hours)
    return (
        db.query(News)
        .join(NewsCategory)
        .filter(NewsCategory.category_id == category_id)
        .filter(News.publishedDate >= twelve_hours_ago)
        .all()
    )



def get_news_for_video(db: Session, category_id: int, hours: int = 12):
    if hours == 0 or hours is None:
        return []
    # Calculate the time for filtering
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    # Perform the query
    result = (
        db.query(
            News.title,
            Media.fileName,
            func.group_concat(Keyword.name).label('keywords')
        )
        .join(NewsCategory, NewsCategory.news_id == News.id)
        .join(NewsMedia, NewsMedia.news_id == News.id)
        .join(Media, NewsMedia.media_id == Media.id)
        .join(NewsKeywords, NewsKeywords.news_id == News.id)
        .join(Keyword, NewsKeywords.keyword_id == Keyword.id)
        .filter(NewsCategory.category_id == category_id)
        .filter(News.publishedDate >= time_threshold)
        .group_by(News.id, Media.fileName)
        .all()
    )

    # Format the results as a list of dictionaries
    news_with_media = [
        {"title": title, "url": url, "keywords": keywords.split(',')}
        for title, url, keywords in result
    ]

    return news_with_media



def get_news_by_keyword(db: Session, keyword_id: int):
    # Assuming there's a relationship defined between News and NewsCategory
    # This will join News with NewsCategory and filter by the provided category_id
    # Finally, it will return a list of News objects
    return (
        db.query(News)
        .join(NewsKeywords)
        .filter(NewsKeywords.keyword_id == keyword_id)
        .all()
    )


#################################### NewsAffiliates ####################################


def get_news_affiliates(db: Session, news_id: int, news_corporation_id: int, external_link: str):
    return (
        db.query(NewsAffiliates)
        .filter(NewsAffiliates.news_id == news_id, NewsAffiliates.newsCorporation_id == news_corporation_id, NewsAffiliates.externalLink == external_link)
        .first()
    )


def create_news_affiliates(db: Session, news_id: int, corporation_id: int, external_link: str):
    news_affiliate = get_news_affiliates(db, news_id, corporation_id, external_link)
    if not news_affiliate:
        news_affiliate = NewsAffiliates(news_id=news_id, newsCorporation_id=corporation_id, externalLink=external_link)
        db.add(news_affiliate)
        db.commit()
        db.refresh(news_affiliate)
    return news_affiliate


def get_news_corporations(db: Session, corporation_id:int):
    return db.query(NewsCorporations).filter(NewsCorporations.id == corporation_id).first()

def get_news_by_user_following(db: Session, user_id: int, hours_ago: int = 24):
    def filter_by_time(query, hours_ago):
        if hours_ago > 0:
            datetime_hours_ago = datetime.utcnow() - timedelta(hours=hours_ago)
            return query.filter(News.publishedDate >= datetime_hours_ago)
        return query

    def get_interested_news(join_model, join_condition, following_model, following_condition):
        query = (
            db.query(News)
            .join(join_model, join_condition)
            .join(following_model, following_condition)
            .filter(following_model.user_id == user_id)
        )
        query = filter_by_time(query, hours_ago)
        return query.order_by(News.createdAt.desc()).all()

    # Assuming the relationships and foreign keys are set up as described in your ORM models
    interested_news_by_category = get_interested_news(
        NewsCategory, NewsCategory.news_id == News.id,
        UserCategoryFollowing, UserCategoryFollowing.category_id == NewsCategory.category_id
    )

    interested_news_by_keyword = get_interested_news(
        NewsKeywords, NewsKeywords.news_id == News.id,
        UserKeywordFollowing, UserKeywordFollowing.keyword_id == NewsKeywords.keyword_id
    )

    all_interested_news = interested_news_by_category + interested_news_by_keyword
    return all_interested_news