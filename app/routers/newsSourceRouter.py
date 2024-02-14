from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.sql.annotation import Annotated

from app.config.dependencies import db_dependency
from app.data.newsSourceData import get_user_all_newsSource_preferences, get_all_news_sources_db
from app.routers.userRouter import user_dependency
from app.services.authService import get_current_user

router = APIRouter(prefix="/newsSource", tags=["newsSource"])
limiter = Limiter(key_func=get_remote_address)

@router.get("/get-all")
async def get_all_news_sources(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    return await get_all_news_sources_db()

@router.get("/get-users-preference")
async def get_user_news_source_preference(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    #1 is for preference
    return await get_user_all_newsSource_preferences(user["id"],1)


@router.get("/get-users-blacklist")
async def get_user_news_source_blacklist(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    #0 is for blacklist
    return await get_user_all_newsSource_preferences(user["id"],0)