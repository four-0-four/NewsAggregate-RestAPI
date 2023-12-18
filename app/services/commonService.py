from sqlalchemy.orm import Session
from app.models.common import Media

# app/controllers/auth_controller.py
from app.models.common import Media, Keyword, Category


async def get_media_by_name_and_type(
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


async def delete_media(db: Session, media_id: int):
    media_item = db.query(Media).filter(Media.id == media_id).first()
    if media_item:
        db.delete(media_item)
        db.commit()


async def save_media(db: Session, file_name: str, file_type: str, file_extension: str):
    new_media = Media(type=file_type, fileName=file_name, fileExtension=file_extension)
    db.add(new_media)
    db.commit()
    return new_media


async def get_keyword(db: Session, keyword: str):
    keyword = db.query(Keyword).filter(Keyword.name == keyword).first()
    return keyword


async def add_keyword(db: Session, keyword: str):
    new_keyword = Keyword(name=keyword)
    db.add(new_keyword)
    db.commit()
    return new_keyword


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


async def add_category_db(db: Session, category: str):
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
