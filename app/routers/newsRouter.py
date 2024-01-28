from fastapi import Request, UploadFile, File, Form
from app.config.dependencies import db_dependency
from app.data.newsData import fetch_news_by_id, get_category_by_topic, get_keyword, \
    get_news_by_keyword, get_news_by_category, get_category_by_parentID, \
    get_news_by_user_following
from app.models.news import NewsInput, NewsDescription
from app.services.locationService import find_city_by_name, find_continent_by_country, find_province_by_name, \
    find_country_by_name, add_news_location
from app.services.writerService import validate_writer
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import add_keyword, get_category, add_category_db, add_media_by_url_to_db, \
    get_media_by_url, add_news_categories_db, get_category_by_id
from app.services.newsService import add_news_db, create_news_keyword, get_news_by_title, delete_news_by_title, \
    create_news_media, get_news_for_video, get_news_affiliates, create_news_affiliates, get_news_corporations, \
    get_news_for_newsCard, get_news_by_id, get_news_information, add_news_from_newsInput,\
    format_newscard
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
    return await add_news_from_newsInput(db, news_input);


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
    rows = await fetch_news_by_id(news_id)
    if not rows:
        raise HTTPException(status_code=404, detail="News not found")

    formatted_news = format_newscard(rows)
    return formatted_news[0] if formatted_news else None


@router.get("/user/get")
async def get_news(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    # check if title is unique
    all_interested_news = await get_news_by_user_following(user["id"])
    formatted_newscard = format_newscard(all_interested_news)
    return formatted_newscard




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

    category = await get_category_by_topic(topic)
    if category:
        news = await get_news_by_category(category['id'], 24)
        news_card = format_newscard(news)
        return news_card

    keyword = await get_keyword(topic)
    if keyword and keyword is not None:
        news = await get_news_by_keyword(keyword['id'], 24)
        news_card = format_newscard(news)
        return news_card

    return []

