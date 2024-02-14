from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.sql.annotation import Annotated
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.config.dependencies import db_dependency
from app.data.preferencData import add_user_blacklist, remove_user_blacklist
from app.routers.userRouter import user_dependency
from app.services.authService import get_current_user
from app.services.preferenceService import reset_preference_for_user, \
    remove_user_news_source_preference, add_user_news_source_preference, add_user_news_blacklist, \
    remove_user_news_blacklist

router = APIRouter(prefix="/preference", tags=["preference"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/reset_preference")
async def add_news_source_preference_for_user(request: Request, user: user_dependency, db: db_dependency):
    try:
        await reset_preference_for_user(user)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        # Log the error or handle it as needed
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add_news_source_preference")
async def add_news_source_preference_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    try:
        await add_user_news_source_preference(user["id"],news_source_id)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        # Log the error or handle it as needed
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete_news_source_preference")
async def delete_news_source_preference_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    try:
        await remove_user_news_source_preference(user["id"], news_source_id)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        # Log the error or handle it as needed
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add_news_source_blacklist")
async def add_news_source_blacklist_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    try:
        await add_user_news_blacklist(user["id"],news_source_id)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        # Log the error or handle it as needed
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete_news_source_blacklist")
async def delete_news_source_blacklist_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    try:
        await remove_user_news_blacklist(user["id"], news_source_id)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        # Log the error or handle it as needed
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add_news_source_blacklist")
async def add_news_source_blacklist_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    return True

@router.post("/delete_news_source_blacklist")
async def delete_news_source_blacklist_for_user(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        news_source_id: int):
    return True