from sqlalchemy.orm import Session
from app.models.common import Media
# app/controllers/auth_controller.py
from fastapi import UploadFile
from app.util.fileUpload import upload_to_spaces
from app.services.commonService import save_media
from fastapi import UploadFile, HTTPException
from secrets import token_hex
from app.models.common import Media, Keyword, Category
import magic  # Ensure python-magic is installed

ALLOWED_MIME_TYPES = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]  # Add allowed MIME types
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def upload_media(db: Session, file_type: str, file: UploadFile):
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


async def save_media(db: Session, file_name: str, file_type: str, file_extension: str):
    new_media = Media(type=file_type, fileName=file_name, fileExtension=file_extension)
    db.add(new_media)
    db.commit()
    return new_media


async def get_keyword(db: Session, keyword_id: int):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    return keyword

async def add_keyword(db: Session, keyword: str):
    new_keyword = Keyword(name=keyword)
    db.add(new_keyword)
    db.commit()
    return {"message": "Keyword added successfully"}

async def update_keyword(db: Session, keyword: str, new_keyword: str):
    existing_keyword = db.query(Keyword).filter(Keyword.name == keyword).first()
    if existing_keyword is None:
        return {"message": "Keyword not found"}
    existing_keyword.name = new_keyword
    db.commit()
    return {"message": "Keyword updated successfully"}

async def delete_keyword(db: Session, keyword: str):
    existing_keyword = db.query(Keyword).filter(Keyword.name == keyword).first()
    if existing_keyword is None:
        return {"message": "Keyword not found"}
    db.delete(existing_keyword)
    db.commit()
    return {"message": "Keyword deleted successfully"}

async def add_category(db: Session, category: str):
    new_category = Category(name=category)
    db.add(new_category)
    db.commit()
    return {"message": "Category added successfully"}

async def update_category(db: Session, category: str, new_category: str):
    existing_category = db.query(Category).filter(Category.name == category).first()
    if existing_category is None:
        return {"message": "Category not found"}
    existing_category.name = new_category
    db.commit()
    return {"message": "Category updated successfully"}

async def delete_category(db: Session, category: str):
    existing_category = db.query(Category).filter(Category.name == category).first()
    if existing_category is None:
        return {"message": "Category not found"}
    db.delete(existing_category)
    db.commit()
    return {"message": "Category deleted successfully"}

async def get_category(db: Session, category: str):
    existing_category = db.query(Category).filter(Category.name == category).first()
    if existing_category is None:
        return {"message": "Category not found"}
    return {"message": "Got category successfully", "category": existing_category.name}

async def get_sub_category(db: Session, parent_id: int):
    sub_categories = db.query(Category).filter(Category.parent_id == parent_id).all()
    return sub_categories