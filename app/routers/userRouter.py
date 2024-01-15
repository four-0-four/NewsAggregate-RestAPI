from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated

from starlette.exceptions import HTTPException

from app.config.dependencies import db_dependency
from app.services.authService import get_current_user
from app.services.commonService import get_category_by_id, get_keyword_byID
from app.services.userService import create_category_following, create_keyword_following, get_all_keyword_following, \
    get_all_category_following

router = APIRouter(prefix="/user", tags=["user"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/get-followings")
async def get_followings(
        request: Request,
        user: user_dependency,
        db: db_dependency):
    all_followings = []
    keyword_followings = get_all_keyword_following(db, user["id"])
    category_followings = get_all_category_following(db, user["id"])

    all_followings.extend(keyword_followings)
    all_followings.extend(category_followings)
    return all_followings


@router.post("/add-following/category")
async def add_following_category(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        category_id: int):
    # check if category exists
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # add it to the following table and get the created entity
    following_entity = create_category_following(db, user["id"], category_id)

    return {"message": "Category following added successfully", "following": following_entity}



@router.post("/add-following/keyword")
async def add_following_keyword(
        request: Request,
        user: user_dependency,
        db: db_dependency,
        keyword_id: int):
    # check if keyword exists
    keyword = get_keyword_byID(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # add it to the following table and get the created entity
    following_entity = create_keyword_following(db, user["id"], keyword_id)

    return {"message": "Keyword following added successfully", "following": following_entity}



