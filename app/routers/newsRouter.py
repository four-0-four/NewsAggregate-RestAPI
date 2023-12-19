from fastapi import Request, UploadFile, File, Form
from app.config.dependencies import db_dependency
from app.models.news import NewsInput
from app.services.writerService import validate_writer
from fastapi import HTTPException, Path, APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated
from app.services.authService import get_current_user
from app.services.commonService import get_keyword, add_keyword
from app.services.newsService import add_news_db, create_news_keyword, get_news_by_title, delete_news_by_title, \
    get_news_category, create_news_category

router = APIRouter(prefix="/news", tags=["news"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/add")
@limiter.limit("10/minute")
async def create_news(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_input: NewsInput):
    # check if title is unique
    existing_news = get_news_by_title(db, news_input.title)
    if existing_news:
        raise HTTPException(status_code=409, detail="News already exists")

    writer_id = news_input.writer_id
    if not validate_writer(db, writer_id):
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

    #add news category to the database if not exists
    existing_news_category = get_news_category(db, news.id, news_input.category_id)
    if not existing_news_category:
        # Add the news category if it does not exist
        existing_news_category = create_news_category(db, news.id, news_input.category_id)

    # await add_medias_to_news(news.id, news_input.media_files)
    return {"message": "News added successfully."}


@router.get("/get")
@limiter.limit("10/minute")
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


@router.delete("/delete")
@limiter.limit("10/minute")
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
