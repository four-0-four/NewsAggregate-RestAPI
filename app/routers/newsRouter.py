from fastapi import Request, UploadFile, File, Form
from app.config.dependencies import db_dependency
from app.models.news import NewsInput, NewsDescription
from app.services.writerService import validate_writer
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import get_keyword, add_keyword, get_category, add_category_db, add_media_by_url_to_db, \
    get_media_by_url, add_news_categories_db
from app.services.newsService import add_news_db, create_news_keyword, get_news_by_title, delete_news_by_title, \
    get_news_category, create_news_category, create_news_media, get_news_by_category, get_news_by_keyword
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

    # adding the news to the database
    news = add_news_db(db, news_input)

    # adding keywords to the the database if not exists
    for keyword in news_input.keywords:
        # Check if the keyword exists
        existing_keyword = get_keyword(db, keyword)
        if not existing_keyword:
            # Add the keyword if it does not exist
            existing_keyword = add_keyword(db, keyword)

        # Add the keyword to the newsKeywords table
        newsKeyword = create_news_keyword(db, news.id, existing_keyword.id)

    # processing the categories and adding them to the database of both news and categories if not exists
    for category in news_input.categories:
        add_news_categories_db(db, category, news.id)


    # adding categories to the database if not exists
    for media_url in news_input.media_urls:
        # Check if the keyword exists
        existing_media = get_media_by_url(db, media_url, news_input.isInternal)
        if not existing_media:
            # Add the keyword if it does not exist
            existing_media = add_media_by_url_to_db(db, media_url, news_input.isInternal)

        newsCategory = create_news_media(db, news.id, existing_media.id)

    # await add_medias_to_news(news.id, news_input.media_files)
    return {"message": "News added successfully."}


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


@router.get("/getByCategory/past12hr")
async def get_news_by_category_last_12hr(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    # check if title is unique
    existing_news = get_news_by_category(db, category_id, 12)
    if not existing_news:
        raise HTTPException(status_code=409, detail="no news found")

    return {"message": "News found successfully.", "news": existing_news}

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


@router.get("/getNewsbyCategoryID")
async def get_news_by_category_id(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    return get_news_by_category(db, category_id)


@router.get("/getNewsbyKeywordID")
async def get_news_by_category_id(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        keyword_id: int):
    return get_news_by_keyword(db, keyword_id)
