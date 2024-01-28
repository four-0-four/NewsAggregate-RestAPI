from datetime import timedelta, datetime

from sqlalchemy import func, and_

from app.data.newsData import get_keyword
from app.models.common import Media, Keyword, NewsCorporations, Category
from app.models.user import UserCategoryFollowing, UserKeywordFollowing
from app.models.writer import Writer
from sqlalchemy.orm import Session, joinedload, subqueryload
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
from app.services.commonService import add_keyword, add_news_categories_db, get_media_by_url, \
    add_media_by_url_to_db
from app.services.locationService import find_city_by_name, find_province_by_name, find_continent_by_country, \
    find_country_by_name, add_news_location
from app.services.writerService import validate_writer
import pytz


#################################### News ####################################


async def add_news_from_newsInput(db: Session, news_input: NewsInput):
    # Validate inputs
    if not news_input.title or not news_input.content:
        raise HTTPException(status_code=400, detail="Title and content are required")

    if len(news_input.keywords) == 0:
        raise HTTPException(status_code=400, detail="Keywords lists cannot be empty")

    if len(news_input.categories) == 0:
        raise HTTPException(status_code=400, detail="Categories lists cannot be empty")

    if len(news_input.media_urls) == 0:
        raise HTTPException(status_code=400, detail="Media URLs lists cannot be empty")

    # check if title is unique
    existing_news = get_news_by_title(db, news_input.title)
    if existing_news:
        raise HTTPException(status_code=409, detail="News already exists")

    writer_id = news_input.writer_id
    if writer_id and not validate_writer(db, writer_id):
        raise HTTPException(status_code=404, detail="Writer not found")

    # Convert publishedDate from EST to UTC
    if news_input.publishedDate:
        # Assuming news_input.publishedDate is a naive datetime object in Eastern Time
        eastern = pytz.timezone('America/Toronto')

        # Localize the naive datetime object to Eastern Time
        eastern_time = eastern.localize(news_input.publishedDate)

        # Check if the date falls within Daylight Saving Time
        is_dst = bool(eastern_time.dst())
        if is_dst:
            # If DST is in effect, convert to EDT (UTC-4)
            utc_time = eastern_time.astimezone(pytz.timezone('UTC'))
        else:
            # If DST is not in effect, convert to EST (UTC-5)
            utc_time = eastern_time.astimezone(pytz.timezone('UTC'))

        # Update the publishedDate to UTC time
        news_input.publishedDate = utc_time

    # adding the news to the database
    news = add_news_db(db, news_input)

    # adding keywords to the the database if not exists
    for keyword in news_input.keywords:
        # Check if the keyword exists
        existing_keyword = await get_keyword(keyword)
        if not existing_keyword:
            # Add the keyword if it does not exist
            existing_keyword = add_keyword(db, keyword)

        # Add the keyword to the newsKeywords table
        newsKeyword = create_news_keyword(db, news.id, existing_keyword.id)

    # processing the categories and adding them to the database of both news and categories if not exists
    for category in news_input.categories:
        add_news_categories_db(db, category, news.id)


    # adding media url
    for media_url in news_input.media_urls:
        # Check if the keyword exists
        existing_media = get_media_by_url(db, media_url, news_input.isInternal)
        if not existing_media:
            # Add the keyword if it does not exist
            existing_media = add_media_by_url_to_db(db, media_url, news_input.isInternal)

        newsCategory = create_news_media(db, news.id, existing_media.id)


    # addding news affiliat
    corporation_exists = get_news_corporations(db, news_input.newsCorporationID)
    if corporation_exists:
        existing_news_affiliates = get_news_affiliates(db, news.id, news_input.newsCorporationID, news_input.externalLink)
        if not existing_news_affiliates:
            existing_news_affiliates = create_news_affiliates(db, news.id, news_input.newsCorporationID, news_input.externalLink)
    else:
        raise HTTPException(status_code=404, detail="News Corporation not found")


    # adding news location
        # Process locations and add to the database
    for location_name in news_input.locations:  # Assuming locations is a list of strings in NewsInput
        # Initialize IDs
        city_id, province_id, country_id, continent_id = None, None, None, None

        # Check if location exists as a city
        city = find_city_by_name(db, location_name)
        if city:
            city_id = city.id
            province_id = city.province_id
            country_id = city.country_id
            # Find the continent for the country
            continent = find_continent_by_country(db, country_id)
            continent_id = continent.id if continent else None
        else:
            # Check if location exists as a province
            province = find_province_by_name(db, location_name)
            if province:
                province_id = province.id
                country_id = province.country_id
                # Find the continent for the country
                continent = find_continent_by_country(db, country_id)
                continent_id = continent.id if continent else None
            else:
                # Check if location exists as a country
                country = find_country_by_name(db, location_name)
                if country:
                    country_id = country.id
                    # Find the continent for the country
                    continent = find_continent_by_country(db, country_id)
                    continent_id = continent.id if continent else None

        # If any location data was found, add it to the NewsLocation table
        if city_id or province_id or country_id or continent_id:
            add_news_location(db, news.id, continent_id, country_id, province_id, city_id)


    # await add_medias_to_news(news.id, news_input.media_files)
    return {"message": "News added successfully."}


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


def get_news_by_id(db: Session, news_id: int):
    return db.query(News).filter(News.id == news_id).first()


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

        # Delete associated NewsAffiliates
        db.query(NewsAffiliates).filter(NewsAffiliates.news_id == news.id).delete()

        # Delete associated NewsLocations
        db.query(NewsLocation).filter(NewsLocation.news_id == news.id).delete()

        # Now delete the news item itself
        db.delete(news)
        db.commit()
        return news

    return None


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

def get_news_by_user_following(db: Session, user_id: int, hours_ago: int = 24, page: int = 1, page_size: int = 20):
    datetime_hours_ago = datetime.utcnow() - timedelta(hours=hours_ago)

    # Calculate the offset (number of records to skip)
    offset = (page - 1) * page_size

    # Combined query for categories and keywords with eager loading for related entities
    query = (
        db.query(News)
        .filter(News.publishedDate >= datetime_hours_ago)
        .join(NewsCategory, NewsCategory.news_id == News.id, isouter=True)
        .join(UserCategoryFollowing,
              and_(UserCategoryFollowing.category_id == NewsCategory.category_id,
                   UserCategoryFollowing.user_id == user_id),
              isouter=True)
        .join(NewsKeywords, NewsKeywords.news_id == News.id, isouter=True)
        .join(UserKeywordFollowing,
              and_(UserKeywordFollowing.keyword_id == NewsKeywords.keyword_id,
                   UserKeywordFollowing.user_id == user_id),
              isouter=True)
        .options(
            joinedload(News.categories),
            joinedload(News.keywords),
            joinedload(News.media),
            subqueryload(News.affiliates)
        )
        .order_by(News.createdAt.desc())
        .limit(page_size)
        .offset(offset)
    )

    return query.all()



def get_news_information(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        newsCard = {
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "content": news.content,
            "publishedDate": news.publishedDate,
            "language_id": news.language_id,
            "isInternal": news.isInternal,
            "isPublished": news.isPublished,
            "createdAt": news.createdAt,
            "updatedAt": news.updatedAt,
            "categories": [],
            "keywords": [],
            "media": [],
            "from": "",
            "fromImage": ""
        }

        # Get the categories
        categories_of_news = db.query(Category).join(
            NewsCategory, NewsCategory.category_id == Category.id
        ).filter(NewsCategory.news_id == news.id).all()
        newsCard["categories"] = [category.name for category in categories_of_news]

        # Get the keywords
        keywords_of_news = db.query(Keyword).join(
            NewsKeywords, NewsKeywords.keyword_id == Keyword.id
        ).filter(NewsKeywords.news_id == news.id).all()
        newsCard["keywords"] = [keyword.name for keyword in keywords_of_news]

        # Get the media
        media_of_news = db.query(Media).join(
            NewsMedia, NewsMedia.media_id == Media.id
        ).filter(NewsMedia.news_id == news.id).all()
        newsCard["media"] = [media.fileName for media in media_of_news]

        # Get the affiliates
        affiliates_of_news = db.query(NewsCorporations.name, NewsCorporations.logo).join(
            NewsAffiliates, NewsAffiliates.newsCorporation_id == NewsCorporations.id
        ).filter(NewsAffiliates.news_id == news.id).all()
        if affiliates_of_news:
            first_affiliate = affiliates_of_news[0]
            newsCard["from"] = first_affiliate.name
            newsCard["fromImage"] = first_affiliate.logo

        return newsCard

    return None

def get_news_for_newsCard(db: Session, listOfNews):
    newsCards = []
    for news in listOfNews:
        newsCards.append(get_news_information(db, news.id))

    return newsCards


def format_newscard(rows: List[dict]) -> List[dict]:
    if not rows:
        return []

    final_output = []
    current_news = {}

    for row in rows:
        if row['title'] != current_news.get('title'):
            if current_news:
                # Convert sets to lists before appending
                current_news['media'] = list(current_news['media'])
                final_output.append(current_news)

            current_news = {k: v for k, v in row.items() if
                            k not in ['category_name', 'keyword_name', 'fileName', 'corporation_name', 'logo']}

            # Initialize sets for categories, keywords, and media to avoid duplicates
            current_news['media'] = {row['fileName']}

            # Handle affiliate (news corporation) data
            if row['corporation_name']:
                current_news['from'] = row['corporation_name']
                current_news['fromImage'] = row['logo']
        else:
            if row['fileName']:
                current_news['media'].add(row['fileName'])

    # Don't forget to add the last news item after the loop
    if current_news:
        current_news['media'] = list(current_news['media'])
        final_output.append(current_news)

    return final_output