from datetime import timedelta, datetime

from sqlalchemy import func, and_

from app.data.newsData import get_entity, add_entity
from app.models.common import Media, entity, NewsCorporations, Category
from app.models.writer import Writer
from sqlalchemy.orm import Session, joinedload, subqueryload
from app.models.news import (
    NewsLocation,
    NewsCategory,
    Newsentities,
    NewsAffiliates,
    NewsMedia,
)
from typing import List
from fastapi import HTTPException
from app.models.news import News, NewsInput
from app.services.commonService import add_news_categories_db, get_media_by_url, \
    add_media_by_url_to_db
from app.services.locationService import find_city_by_name, find_province_by_name, find_continent_by_country, \
    find_country_by_name, add_news_location
from app.services.writerService import validate_writer


#################################### News ####################################


async def add_news_from_newsInput(db: Session, news_input: NewsInput):
    # Validate inputs
    if not news_input.title or not news_input.content:
        raise HTTPException(status_code=400, detail="Title and content are required")

    #TODO
    #if len(news_input.entities) == 0:
    #    raise HTTPException(status_code=400, detail="entities lists cannot be empty")

    if len(news_input.categories) == 0:
        raise HTTPException(status_code=400, detail="Categories lists cannot be empty")

    # TODO
    #if len(news_input.media_urls) == 0:
    #    raise HTTPException(status_code=400, detail="Media URLs lists cannot be empty")

    # check if title is unique
    existing_news = get_news_by_title(db, news_input.title)
    if existing_news:
        raise HTTPException(status_code=409, detail="News already exists")

    writer_id = news_input.writer_id
    if writer_id and not validate_writer(db, writer_id):
        raise HTTPException(status_code=404, detail="Writer not found")

    # adding the news to the database
    news = add_news_db(db, news_input)

    # adding entities to the the database if not exists
    for entity in news_input.entities:
        # Check if the entity exists
        existing_entity = await get_entity(entity)
        if not existing_entity:
            # Add the entity if it does not exist
            # TODO: change the type of added entity
            await add_entity(entity,"test")
            existing_entity = await get_entity(entity)

        # Add the entity to the newsEntities table
        newsentity = create_news_entity(db, news.id, existing_entity["id"])

    # processing the categories and adding them to the database of both news and categories if not exists
    for category in news_input.categories:
        add_news_categories_db(db, category, news.id)


    # adding media url
    for media_url in news_input.media_urls:
        # Check if the entity exists
        existing_media = get_media_by_url(db, media_url, news_input.isInternal)
        if not existing_media:
            # Add the entity if it does not exist
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
        shortSummary=news_input.shortSummary,
        longSummary=news_input.longSummary,
        content=news_input.content,
        publishedDate=news_input.publishedDate,
        language_id=news_input.language_id,
        isInternal=news_input.isInternal,
        ProcessedForIdentity=news_input.ProcessedForIdentity
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

        # Delete associated Newsentities
        db.query(Newsentities).filter(Newsentities.news_id == news.id).delete()

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


def create_news_entity(db: Session, news_id: int, entity_id: int):
    news_entity = get_news_entity(db, news_id, entity_id)
    if not news_entity:
        news_entity = Newsentities(news_id=news_id, entity_id=entity_id)
        db.add(news_entity)
        db.commit()
        db.refresh(news_entity)
        return news_entity
    return news_entity


def get_news_entity(db: Session, news_id: int, entity_id: int):
    return (
        db.query(Newsentities)
        .filter(Newsentities.news_id == news_id, Newsentities.entity_id == entity_id)
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
            Media.mainImage,
            func.group_concat(entity.name).label('entities')
        )
        .join(NewsCategory, NewsCategory.news_id == News.id)
        .join(NewsMedia, NewsMedia.news_id == News.id)
        .join(Media, NewsMedia.media_id == Media.id)
        .join(Newsentities, Newsentities.news_id == News.id)
        .join(entity, Newsentities.entity_id == entity.id)
        .filter(NewsCategory.category_id == category_id)
        .filter(News.publishedDate >= time_threshold)
        .group_by(News.id, Media.mainImage)
        .all()
    )

    # Format the results as a list of dictionaries
    news_with_media = [
        {"title": title, "url": url, "entities": entities.split(',')}
        for title, url, entities in result
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


def get_news_information(db: Session, news_id: int):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        newsCard = {
            "id": news.id,
            "title": news.title,
            "shortSummary": news.shortSummary,
            "longSummary": news.longSummary,
            "content": news.content,
            "publishedDate": news.publishedDate,
            "language_id": news.language_id,
            "isInternal": news.isInternal,
            "ProcessedForIdentity": news.ProcessedForIdentity,
            "createdAt": news.createdAt,
            "updatedAt": news.updatedAt,
            "categories": [],
            "entities": [],
            "media": [],
            "from": "",
            "fromImage": ""
        }

        # Get the categories
        categories_of_news = db.query(Category).join(
            NewsCategory, NewsCategory.category_id == Category.id
        ).filter(NewsCategory.news_id == news.id).all()
        newsCard["categories"] = [category.name for category in categories_of_news]

        # Get the entities
        entities_of_news = db.query(entity).join(
            Newsentities, Newsentities.entity_id == entity.id
        ).filter(Newsentities.news_id == news.id).all()
        newsCard["entities"] = [entity.name for entity in entities_of_news]

        # Get the media
        media_of_news = db.query(Media).join(
            NewsMedia, NewsMedia.media_id == Media.id
        ).filter(NewsMedia.news_id == news.id).all()
        newsCard["media"] = [media.mainImage for media in media_of_news]

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


def get_oldest_news_time(news_cards: List[dict]) -> str:
    """
    Gets the published date of the oldest news item in the list.

    Args:
        news_cards: A list of news items, each represented as a dictionary.

    Returns:
        The published date of the oldest news item as a string.
        If the list is empty, returns an empty string.
    """
    if not news_cards:
        return ""

    # No need to parse 'publishedDate' as it's already a datetime object
    oldest_date = datetime.max  # Initialize with the maximum possible datetime

    for card in news_cards:
        # Directly compare the datetime objects
        card_date = card['publishedDate']
        if card_date < oldest_date:
            oldest_date = card_date

    # If no date was found (list was empty or no valid dates), return an empty string
    if oldest_date == datetime.max:
        return ""

    # Convert the oldest date back to string if necessary
    return oldest_date.strftime('%Y-%m-%d %H:%M:%S')


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
                            k not in ['category_name', 'entity_name', 'mainImage', 'corporationName', 'corporationLogo']}

            # Initialize sets for categories, entities, and media to avoid duplicates
            current_news['media'] = {row['mainImage']}

            # Handle affiliate (news corporation) data
            if row['corporationName']:
                current_news['from'] = row['corporationName']
                current_news['fromImage'] = row['corporationLogo']
        else:
            if row['mainImage']:
                current_news['media'].add(row['mainImage'])

    # Don't forget to add the last news item after the loop
    if current_news:
        current_news['media'] = list(current_news['media'])
        final_output.append(current_news)

    return final_output