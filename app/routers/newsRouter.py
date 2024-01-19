from fastapi import Request, UploadFile, File, Form
from app.config.dependencies import db_dependency
from app.models.news import NewsInput, NewsDescription
from app.services.locationService import find_city_by_name, find_continent_by_country, find_province_by_name, \
    find_country_by_name, add_news_location
from app.services.writerService import validate_writer
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import get_keyword, add_keyword, get_category, add_category_db, add_media_by_url_to_db, \
    get_media_by_url, add_news_categories_db, get_category_by_id, get_category_by_parentID, get_category_by_topic
from app.services.newsService import add_news_db, create_news_keyword, get_news_by_title, delete_news_by_title, \
    create_news_media, get_news_by_category, get_news_by_keyword, \
    get_news_for_video, get_news_affiliates, create_news_affiliates, get_news_corporations, get_news_by_user_following, \
    get_news_for_newsCard, get_news_by_id, get_news_information, get_news_by_category_or_keyword, \
    add_news_from_newsInput
from app.services.newsAnalyzer import extract_keywords

router = APIRouter(prefix="/news", tags=["news"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/add")
async def create_news(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_input: NewsInput):
    return add_news_from_newsInput(db, news_input);


@router.get("/get")
async def get_news(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_title: str):
    # check if title is unique
    existing_news = get_news_by_title(db, news_title)
    if not existing_news:
        raise HTTPException(status_code=409, detail="News does not exists")

    return {"message": "News found successfully.", "news_id": existing_news.id}



@router.get("/getByID")
async def get_news_byID(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_id: int):
    news = get_news_by_id(db, news_id)
    if not news:
        raise HTTPException(status_code=409, detail="News does not exists")
    return get_news_information(db, news.id)


@router.get("/user/get")
async def get_news(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    # check if title is unique
    all_interested_news = get_news_by_user_following(db, user["id"])
    full_news = get_news_for_newsCard(db, all_interested_news)
    return full_news


@router.get("/getDifferentNewsForTopicPage")
async def get_different_news_for_topic_page(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        parent_category_id: int):
    # Get categories based on parent_category_id
    categories = get_category_by_parentID(db, parent_category_id)

    # Initialize an empty dictionary to store news for each category
    variety_news_based_on_categories = {}

    # Initialize an empty list to store category names
    category_names = []

    for category in categories:
        # Add category name to the list
        category_names.append(category.name)

        # Call get_news_by_category function for each category and store the result
        news_for_category = get_news_by_category(db, category.id, hours=1000, limit=3)
        variety_news_based_on_categories[category.name] = get_news_for_newsCard(db, news_for_category)

    # Return category names and variety_news_based_on_categories as a response
    return {
        "categories": category_names,
        "news": variety_news_based_on_categories
    }




@router.get("/getByCategory")
async def get_news_by_category_and_past_hour(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int,
        past_hours: int):
    # check if title is unique
    existing_news = get_news_by_category(db, category_id, past_hours)
    if not existing_news:
        raise HTTPException(status_code=409, detail="no news found")
    complete_news = get_news_for_newsCard(db, existing_news)
    return {"message": "News found successfully.", "news": complete_news}


@router.get("/getForVideo/past12hr")
async def get_news_for_video_last_12hr(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    existing_news = get_news_for_video(db, category_id, 12)
    category = get_category_by_id(db, category_id)
    return {"category": category.name, "news": existing_news}


@router.get("/getForVideo/past24hr")
async def get_news_for_video_last_24hr(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    # check if title is unique
    existing_news = get_news_for_video(db, category_id, 24)
    category = get_category_by_id(db, category_id)
    return {"category": category.name, "news": existing_news}


@router.delete("/delete")
async def delete_news(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_title: str):
    # check if title is unique
    existing_news = delete_news_by_title(db, news_title)
    if not existing_news:
        raise HTTPException(status_code=409, detail="News does not exists")

    return {"message": "News deleted successfully.", "news_id": existing_news.id}


@router.get("/acquireKeywords")
async def acquire_keywords(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        newsDescription: NewsDescription):

    return extract_keywords(newsDescription.description)



@router.get("/getNewsbyKeywordID")
async def get_news_by_category_id(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        keyword_id: int):
    return get_news_by_keyword(db, keyword_id)



@router.get("/getNewsbyTopic")
async def get_news_by_topid(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        topic: str):

    category = get_category_by_topic(db, topic)
    keyword = get_keyword(db, topic)
    if category and keyword:
        news = get_news_by_category_or_keyword(db, category.id, keyword.id)
    elif category:
        news = get_news_by_category(db, category.id, hours=1000, limit=10)
    elif keyword:
        news = get_news_by_keyword(db, keyword.id)
    else:
        raise HTTPException(status_code=404, detail="Topic not found")

    return get_news_for_newsCard(db, news)

