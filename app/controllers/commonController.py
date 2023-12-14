# app/controllers/auth_controller.py
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from typing import Annotated
from app.config.dependencies import get_db,oauth2_bearer, db_dependency
from app.services.authService import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.util.fileUpload import upload_to_spaces
from app.services.commonService import save_media
from fastapi import UploadFile, HTTPException
from secrets import token_hex
import magic  # Ensure python-magic is installed


router = APIRouter(prefix="/common", tags=["common"])
limiter = Limiter(key_func=get_remote_address)
user_dependency = Annotated[dict, Depends(get_current_user)]

ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]  # Add allowed MIME types
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/upload/")
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
    #save_media(db: Session, file_name: str, file_type: str, file_extension: str)
    media_record = await save_media(db, file_name, file_type, file_ext)

    return {"file_name": file_name, "id": media_record.id}
