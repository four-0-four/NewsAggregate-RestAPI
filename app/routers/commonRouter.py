# app/controllers/auth_controller.py
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from typing import Annotated
from app.config.dependencies import db_dependency
from app.services.authService import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.services.commonService import add_keyword, save_media, update_keyword, delete_keyword, add_category, update_category, delete_category, get_keyword, get_sub_category, get_category
from app.util.fileUpload import upload_to_spaces, delete_from_spaces, DeleteError
from fastapi import UploadFile, HTTPException
from secrets import token_hex
from app.services.commonService import get_media_by_name_and_type, delete_media
import magic  # Ensure python-magic is installed

router = APIRouter(prefix="/common", tags=["common"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]
ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]  # Add allowed MIME types
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/file/upload/")
@limiter.limit("10/minute")
async def upload_document(request: Request, user: user_dependency, db: db_dependency, file_type: str = Form(...),file: UploadFile = File(...)):
    # Read the contents of the file
    contents = await file.read()

    # Check the file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds the allowed limit.")

    # Get MIME type of the file
    mime_type = magic.from_buffer(contents, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type.")

    # Reset file to the beginning after reading
    file.file.seek(0)

    # Upload the file to DigitalOcean Spaces
    file_ext = file.filename.split(".")[-1]
    file_name = token_hex(16)
    file_path = file_type + "/"
    url = await upload_to_spaces(file_name, file_path, file_ext, file)
 
    # Save the URL in the database
    media_record = await save_media(db, file_name, file_type, file_ext)

    return {"file_name": file_name, "id": media_record.id}

@router.delete("/file/delete/")
@limiter.limit("10/minute")
async def delete_document(request: Request, user: user_dependency, db: db_dependency, file_type: str, file_name: str, file_ext: str):
    # Construct the file path (assuming file_name includes the file extension)
    file_path = f"{file_type}/{file_name}.{file_ext}"

    # Delete the file from DigitalOcean Spaces
    try:
        await delete_from_spaces(file_path)
    except DeleteError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Delete the file record from the database (assuming get_media_by_name_and_type and delete_media are defined)
    file_info = await get_media_by_name_and_type(db, file_type, file_name, file_ext)
    if file_info:
        await delete_media(db, file_info.id)

    return {"detail": "File deleted successfully."}

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