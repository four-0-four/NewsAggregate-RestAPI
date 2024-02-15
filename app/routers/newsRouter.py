from fastapi import Request
from app.config.dependencies import db_dependency
from app.data.newsData import fetch_news_by_id, get_category_by_topic, get_keyword, \
    get_news_by_keyword, get_news_by_category, get_news_by_user_following
from app.models.news import NewsInput, NewsDescription
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import get_category_by_id
from app.services.newsService import get_news_by_title, delete_news_by_title, \
    get_news_for_video, get_news_for_newsCard, add_news_from_newsInput, format_newscard, get_oldest_news_time
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
        last_news_time: str,
        number_of_articles_to_fetch: int,
        db: db_dependency):
    # check if title is unique
    all_interested_news = await get_news_by_user_following(user["id"], last_news_time, number_of_articles_to_fetch * 2)
    print(all_interested_news[:number_of_articles_to_fetch])
    formatted_newscard = format_newscard(all_interested_news[:number_of_articles_to_fetch])
    new_last_news_time = get_oldest_news_time(formatted_newscard)
    return {"news": formatted_newscard, "last_news_time": new_last_news_time, "load_more": len(all_interested_news)>number_of_articles_to_fetch}




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
    return get_news_by_keyword(db, keyword_id, 10, user["id"])



@router.get("/getNewsbyTopic")
async def get_news_by_topid(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        topic: str,
        last_news_time: str,
        number_of_articles_to_fetch: int):

    category = await get_category_by_topic(topic)
    if category:
        news = await get_news_by_category(category['id'], last_news_time, number_of_articles_to_fetch * 2, user["id"])
        news_card = format_newscard(news[:number_of_articles_to_fetch])
        new_last_news_time = get_oldest_news_time(news_card)
        return {"news": news_card, "last_news_time": new_last_news_time, "load_more": len(news)>number_of_articles_to_fetch}

    keyword = await get_keyword(topic)
    if keyword and keyword is not None:
        news = await get_news_by_keyword(keyword['id'], last_news_time, number_of_articles_to_fetch * 2, user["id"])
        news_card = format_newscard(news[:number_of_articles_to_fetch])
        new_last_news_time = get_oldest_news_time(news_card)
        return {"news": news_card, "last_news_time": new_last_news_time, "load_more": len(news)>number_of_articles_to_fetch}

    return {"news": [], "last_news_time": last_news_time, "load_more": False}

