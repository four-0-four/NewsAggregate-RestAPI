# app/controllers/auth_controller.py
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from typing import Annotated
from app.config.dependencies import db_dependency
from app.services.authService import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.commonService import add_keyword, update_keyword, delete_keyword, upload_media, add_category, update_category, delete_category, get_keyword, get_sub_category, get_category


router = APIRouter(prefix="/common", tags=["common"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/upload/")
@limiter.limit("10/minute")
async def upload_document(request: Request, user: user_dependency, db: db_dependency, file_type: str = Form(...),file: UploadFile = File(...)):
    return upload_media(db, file_type, file)

@router.get("/keyword")
@limiter.limit("10/minute")
async def get_keyword(request: Request, user: user_dependency, db: db_dependency, keyword_id: int):
    return get_keyword(db, keyword_id)

@router.post("/keyword")
@limiter.limit("10/minute")
async def add_keyword(request: Request, user: user_dependency, db: db_dependency, keyword: str):
    return add_keyword(db, keyword)

@router.put("/keyword")
@limiter.limit("10/minute")
async def update_keyword(request: Request, user: user_dependency, db: db_dependency, keyword: str, new_keyword: str):
    return update_keyword(db, keyword, new_keyword)

@router.delete("/keyword")
@limiter.limit("10/minute")
async def delete_keyword(request: Request, user: user_dependency, db: db_dependency, keyword: str):
    return delete_keyword(db, keyword)


@router.get("/category/individual")
@limiter.limit("10/minute")
async def get_category(request: Request, user: user_dependency, db: db_dependency, category: str):
    return get_category(db, category)

@router.get("/category/children")
@limiter.limit("10/minute")
async def get_sub_category(request: Request, user: user_dependency, db: db_dependency, parent_id: int):
    return get_sub_category(db, parent_id)

@router.post("/category")
@limiter.limit("10/minute")
async def add_category(request: Request, user: user_dependency, db: db_dependency, category: str):
    return add_category(db, category)

@router.put("/category")
@limiter.limit("10/minute")
async def update_category(request: Request, user: user_dependency, db: db_dependency, category: str, new_category: str):
    return update_category(db, category, new_category)

@router.delete("/category")
@limiter.limit("10/minute")
async def delete_category(request: Request, user: user_dependency, db: db_dependency, category: str):
    return delete_category(db, category)
