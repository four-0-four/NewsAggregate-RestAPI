from sqlalchemy.orm import Session
from app.models.common import Media
import os

# app/controllers/auth_controller.py
from app.models.common import Media, Keyword, Category


def get_media_by_name_and_type(
    db: Session, file_name: str, file_type: str, file_ext: str
):
    return (
        db.query(Media)
        .filter(
            Media.fileName == file_name,
            Media.type == file_type,
            Media.fileExtension == file_ext,
        )
        .first()
    )


def get_media_by_url(db: Session, url: str, isInternal: bool):
    if isInternal:
        # Extracting fileName, fileExtension, and type from the URL
        mediaparts = url.split('/')
        mediatype = mediaparts[0]
        mediafileName, mediafileExtension = os.path.splitext(mediaparts[1])
        mediafileExtension = mediafileExtension[1:]  # Remove the dot from the extension
        # Query the database
        return db.query(Media).filter_by(type=mediatype, fileName=mediafileName, fileExtension=mediafileExtension).first()
    else:
        # Directly compare the fileName with the URL for external links
        return db.query(Media).filter_by(fileName=url).first()


def add_media_by_url_to_db(db: Session, url: str, isInternal: bool):
    if isInternal:
        # Extracting fileName, fileExtension, and type from the URL
        mediaparts = url.split('/')
        mediatype = mediaparts[0]
        mediafileName, mediafileExtension = os.path.splitext(mediaparts[1])
        mediafileExtension = mediafileExtension[1:]  # Remove the dot from the extension
    else:
        # For external URLs, the entire URL is considered as fileName
        mediatype = None
        mediafileName = url
        mediafileExtension = url.split('.')[-1]

    # Create a new Media instance
    new_media = Media(type=type, fileName=mediafileName, fileExtension=mediafileExtension)
    db.add(new_media)
    db.commit()
    db.refresh(new_media)
    return new_media


def delete_media(db: Session, media_id: int):
    media_item = db.query(Media).filter(Media.id == media_id).first()
    if media_item:
        db.delete(media_item)
        db.commit()


def save_media(db: Session, file_name: str, file_type: str, file_extension: str):
    new_media = Media(type=file_type, fileName=file_name, fileExtension=file_extension)
    db.add(new_media)
    db.commit()
    return new_media


def get_keyword(db: Session, keyword: str):
    keyword = db.query(Keyword).filter(Keyword.name == keyword).first()
    return keyword


def add_keyword(db: Session, keyword: str):
    new_keyword = Keyword(name=keyword)
    db.add(new_keyword)
    db.commit()
    return new_keyword


def add_category_db(db: Session, category_name: str):
    # First, check if the category already exists
    existing_category = db.query(Category).filter(Category.name == category_name).first()

    # If the category does not exist, add it
    if existing_category is None:
        new_category = Category(name=category_name)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)  # Load the data from the database
        return {"message": "Category added successfully", "category": new_category}
    else:
        # If the category already exists, return a message indicating it
        return {"message": "Category already exists, no action taken", "category": existing_category}


def get_category(db: Session, category: str):
    existing_category = db.query(Category).filter(Category.name == category).first()
    if existing_category is None:
        return {"message": "Category not found"}
    return {"message": "Got category successfully", "category": existing_category}