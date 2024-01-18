from sqlalchemy.orm import Session

from app.models.news import NewsCategory


def get_news_category(db: Session, news_id: int, category_id: int):
    return db.query(NewsCategory).filter(NewsCategory.news_id == news_id, NewsCategory.category_id == category_id).first()


def create_news_category(db: Session, news_id: int, category_id: int):
    # Check if the news_category already exists
    existing_news_category = get_news_category(db, news_id, category_id)

    # If it exists, return the existing entry
    if existing_news_category:
        return existing_news_category

    # If it does not exist, create a new instance of NewsCategory
    new_news_category = NewsCategory(news_id=news_id, category_id=category_id)

    # Add the new instance to the session and commit
    db.add(new_news_category)
    db.commit()

    # Refresh to get the data from the database, if necessary
    db.refresh(new_news_category)

    return new_news_category