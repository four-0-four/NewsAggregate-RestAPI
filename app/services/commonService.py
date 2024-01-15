from sqlalchemy.orm import Session
from app.models.common import Media
import os
import re

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
        mediatype = 'external'
        mediafileName = url
        mediafileExtension = 'external'

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

def get_keyword_byID(db: Session, keyword_id: int):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    return keyword


def get_category_by_id(db: Session, category_id:int):
    existing_category = db.query(Category).filter(
        Category.id == category_id,
    ).first()
    return existing_category


def is_category_path_invalid(category_path: str):
    # Regular expression for allowed characters in category names
    valid_name_pattern = re.compile(r'^[A-Za-z0-9-/]+$')

    # Check for consecutive forward slashes
    if '//' in category_path:
        return True

    # Validate the entire path before splitting into categories
    if not valid_name_pattern.match(category_path):
        return True

    # category_path can not be empty
    if len(category_path) == 0:
        return True

def add_news_categories_db(db: Session, category_path: str, news_id: int):
    if is_category_path_invalid(category_path):
        return {"message": "Invalid category path"}

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


def add_category_db(db: Session, category_path: str):
    if is_category_path_invalid(category_path):
        return {"message": "Invalid category path"}

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
    if is_category_path_invalid(category_path):
        return {"message": "Invalid category path"}

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

    # Check if the category is found after going through the loop
    if existing_category is None:
        return {"message": "Category not found"}

    # After finding the category at the last level, return it
    return {"message": "Got category successfully", "category": existing_category}


def delete_last_category(db: Session, category_path: str):
    if is_category_path_invalid(category_path):
        return {"message": "Invalid category path"}

    # Find the last category using similar logic as in get_category
    existing_category = None
    if "/" not in category_path:
        existing_category = db.query(Category).filter(
            Category.name == category_path,
        ).first()
    else:
        categories = category_path.strip("/").split("/")
        parent_id = 0
        for category_name in categories:
            existing_category = db.query(Category).filter(
                Category.name == category_name,
                Category.parent_id == parent_id
            ).first()
            if existing_category:
                parent_id = existing_category.id

    if existing_category is None:
        return {"message": "Category not found"}

    # Delete the found category
    db.delete(existing_category)
    db.commit()

    return {"message": "Category deleted successfully", "category": existing_category}


def delete_all_categories_in_path(db: Session, category_path: str):
    if is_category_path_invalid(category_path):
        return {"message": "Invalid category path"}

    if "/" not in category_path:
        # If the path is a single category, just delete this category
        return delete_last_category(db, category_path)

    categories = category_path.strip("/").split("/")
    parent_id = 0
    for category_name in categories:
        # Find and delete each category in the path
        existing_category = db.query(Category).filter(
            Category.name == category_name,
            Category.parent_id == parent_id
        ).first()

        if existing_category is None:
            return {"message": f"Category '{category_name}' not found in path"}

        # Delete the category and update parent_id for the next iteration
        db.delete(existing_category)
        parent_id = existing_category.id
        db.commit()

    return {"message": "All categories in path deleted successfully"}
