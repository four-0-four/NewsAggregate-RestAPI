from datetime import datetime
from fastapi import Request
from app.config.dependencies import db_dependency
from app.data.newsData import add_news_to_bookmark, check_news_exists_by_id, fetch_news_by_id, fetch_news_by_id_authenticated, get_all_bookmarks_for_user, get_category_by_parentID, get_category_by_topic, get_entity, \
    get_news_by_entity, get_news_by_category, get_news_by_user_following, remove_news_from_bookmark
from app.models.news import NewsInput
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import get_category_by_id
from app.services.newsService import get_news_by_title, delete_news_by_title, \
    get_news_for_video, get_news_for_newsCard, add_news_from_newsInput, format_newscard, get_oldest_news_time
from app.services.newsAnalyzer import extract_entities
from time import time
from asyncio import gather
import random


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



@router.get("/getByIDAuthenticated")
async def get_news_byID_authorized(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_id: int):
    news = await fetch_news_by_id_authenticated(news_id, user["id"])
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    #formatted_news = format_newscard(rows)
    return news if news else None

@router.get("/getByID")
async def get_news_byID(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_id: int):
    news = await fetch_news_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    #formatted_news = format_newscard(rows)
    return news if news else None


@router.get("/user/get")
async def get_news(
        request: Request,
        user: user_dependency,
        last_news_time: str,
        number_of_articles_to_fetch: int,
        db: db_dependency):
    overall_start_time = time()  # Start timing overall process
    
    # check if title is unique
    start_time = time()  # Start timing for get_news_by_user_following
    all_interested_news = await get_news_by_user_following(user["id"], last_news_time, number_of_articles_to_fetch * 2)
    end_time = time()  # End timing for get_news_by_user_following
    print(f"get_news_by_user_following took {end_time - start_time} seconds")
    
    #start_time = time()  # Start timing for format_newscard
    #formatted_newscard = format_newscard(all_interested_news[:number_of_articles_to_fetch])
    #end_time = time()  # End timing for format_newscard
    #print(f"format_newscard took {end_time - start_time} seconds")
    
    start_time = time()  # Start timing for get_oldest_news_time
    new_last_news_time = get_oldest_news_time(all_interested_news)
    end_time = time()  # End timing for get_oldest_news_time
    print(f"get_oldest_news_time took {end_time - start_time} seconds")
    
    overall_end_time = time()  # End timing overall process
    print(f"Overall process took {overall_end_time - overall_start_time} seconds")
    
    return {"news": all_interested_news[:number_of_articles_to_fetch], "last_news_time": new_last_news_time, "load_more": len(all_interested_news)>number_of_articles_to_fetch}

'''
async def get_news(
        request: Request,
        user: user_dependency,
        last_news_time: str,
        number_of_articles_to_fetch: int,
        db: db_dependency):
    # check if title is unique
    all_interested_news = await get_news_by_user_following(user["id"], last_news_time, number_of_articles_to_fetch * 2)
    formatted_newscard = format_newscard(all_interested_news[:number_of_articles_to_fetch])
    new_last_news_time = get_oldest_news_time(formatted_newscard)
    return {"news": formatted_newscard, "last_news_time": new_last_news_time, "load_more": len(all_interested_news)>number_of_articles_to_fetch}
'''



@router.get("/getByCategory")
async def get_news_by_category_and_past_hour(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    # check if title is unique
    now = datetime.now()
    date_string = now.strftime('%Y-%m-%d %H:%M:%S')
    existing_news = await get_news_by_category(category_id, date_string, 10, user["id"])
    if not existing_news:
        raise HTTPException(status_code=409, detail="no news found")
    return {"message": "News found successfully.", "news": existing_news}


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



@router.get("/getNewsbyentityID")
async def get_news_by_category_id(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        entity_id: int):
    return get_news_by_entity(db, entity_id, 10, user["id"])


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
        #news_card = format_newscard(news[:number_of_articles_to_fetch])
        news_card = news[:number_of_articles_to_fetch]
        new_last_news_time = get_oldest_news_time(news_card)
        return {"news": news_card, "last_news_time": new_last_news_time, "load_more": len(news)>number_of_articles_to_fetch}

    entity = await get_entity(topic)
    if entity and entity is not None:
        news = await get_news_by_entity(entity['id'], last_news_time, number_of_articles_to_fetch * 2, user["id"])
        #news_card = format_newscard(news[:number_of_articles_to_fetch])
        news_card = news[:number_of_articles_to_fetch]
        new_last_news_time = get_oldest_news_time(news_card)
        return {"news": news_card, "last_news_time": new_last_news_time, "load_more": len(news)>number_of_articles_to_fetch}

    return {"news": [], "last_news_time": last_news_time, "load_more": False}


@router.get("/explore")
async def get_news_by_topid(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        last_news_time: str,
        parent_category_id: int):

    all_news = []
    number_of_articles_to_fetch = 10
    # get the categories based on the parent_cat_id
    categories = await get_category_by_parentID(parent_category_id)
    
    # Prepare asynchronous tasks for fetching news for each category
    tasks = [
        get_news_by_category(category['id'], last_news_time, number_of_articles_to_fetch * 2, user["id"])
        for category in categories
    ]
    
    # Execute all tasks concurrently and await their results
    results = await gather(*tasks)
    
    all_news = []
    for news in results:
        news_card = news[:number_of_articles_to_fetch]
        all_news.extend(news_card)
        
    # Shuffle the news items to mix them up
    random.shuffle(all_news)
    
    # Determine new last news time from the last fetched batch
    new_last_news_time = get_oldest_news_time(news_card) if all_news else last_news_time
    
    # Determine if more news are available for loading more
    load_more = any(len(news) > 10 for news in results)
    
    return {"news": all_news, "last_news_time": new_last_news_time, "load_more": load_more}


########################BOOKMARKS########################

@router.post("/addNewsToBookmark/")
async def add_news_to_bookmark_route(
        news_id: int,
        user: user_dependency,
        db: db_dependency):
    if(check_news_exists_by_id(news_id) == False):
        raise HTTPException(status_code=400, detail="News does not exists")
    try:
        await add_news_to_bookmark(user['id'], news_id)
        return {"message": "News successfully added to bookmarks."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/removeNewsFromBookmark/")
async def remove_news_from_bookmark_route(
        news_id: int,
        user: user_dependency,
        db: db_dependency):
    if(check_news_exists_by_id(news_id) == False):
        raise HTTPException(status_code=400, detail="News does not exists")
    try:
        await remove_news_from_bookmark(user['id'], news_id)
        return {"message": "News successfully removed from bookmarks."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/getAllBookmarksForUser/")
async def get_all_bookmarks_for_user_route(
        user: user_dependency,
        db: db_dependency):
    try:
        bookmarked_news = await get_all_bookmarks_for_user(user['id'])
        news_card = format_newscard(bookmarked_news)
        return news_card
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

