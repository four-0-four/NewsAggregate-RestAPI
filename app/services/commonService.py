from sqlalchemy.orm import Session
from app.models.common import Media
import os

# app/controllers/auth_controller.py
from app.models.common import Media, Keyword, Category
from app.services.newsService import create_news_category


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


def add_news_categories_db(db: Session, category_path: str, news_id: int):
    # Split the category path into hierarchical components
    categories = category_path.strip("/").split("/")
    category_ids = []
    parent_id = 0  # Start with the root parent_id
    for category_name in categories:
        # Check if the category already exists
        existing_category = db.query(Category).filter(
            Category.name == category_name and Category.parent_id == parent_id
        ).first()

        if existing_category is None:
            # If the category does not exist, add it
            new_category = Category(name=category_name, parent_id=parent_id)
            db.add(new_category)
            db.commit()
            db.refresh(new_category)
            create_news_category(db, news_id, new_category.id)
            category_ids.append(new_category.id)
            parent_id = new_category.id  # Update parent_id for the next level
        else:
            # If the category exists, use its ID as the parent_id for the next level
            create_news_category(db, news_id, existing_category.id)
            category_ids.append(existing_category.id)
            parent_id = existing_category.id

    return {"message": "Category processed successfully", "category_ids": category_ids}


def add_category_db(db: Session, category_path: str, news_id: int):
    # Split the category path into hierarchical components
    categories = category_path.strip("/").split("/")
    category_ids = []
    parent_id = 0  # Start with the root parent_id
    for category_name in categories:
        # Check if the category already exists
        existing_category = db.query(Category).filter(
            Category.name == category_name and Category.parent_id == parent_id
        ).first()

        if existing_category is None:
            # If the category does not exist, add it
            new_category = Category(name=category_name, parent_id=parent_id)
            db.add(new_category)
            db.commit()
            db.refresh(new_category)
            category_ids.append(new_category.id)
            parent_id = new_category.id  # Update parent_id for the next level
        else:
            # If the category exists, use its ID as the parent_id for the next level
            category_ids.append(existing_category.id)
            parent_id = existing_category.id

    return {"message": "Category processed successfully", "category_ids": category_ids}


def get_category(db: Session, category_path: str):
    existing_category = None
    if "/" not in category_path:
        existing_category = db.query(Category).filter(
            Category.name == category_path,
        ).first()
    else:
        # Split the category path into hierarchical components
        categories = category_path.strip("/").split("/")

        parent_id = 0  # Start with the root parent_id
        for category_name in categories:
            # Find the category at this level of the hierarchy
            existing_category = db.query(Category).filter(
                Category.name == category_name,
                Category.parent_id == parent_id
            ).first()

            if existing_category is None:
                # If the category at this level doesn't exist, return not found
                return {"message": "Category not found"}

            # Update parent_id for the next level in the hierarchy
            parent_id = existing_category.id

    # After finding the category at the last level, return it
    return {"message": "Got category successfully", "category": existing_category}
