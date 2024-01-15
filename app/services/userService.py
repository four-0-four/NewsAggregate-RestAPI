from sqlalchemy.orm import Session

from app.models.common import Keyword, Category
from app.models.user import UserCategoryFollowing, UserKeywordFollowing


def get_all_category_following(db: Session, user_id: int):
    userCategoryFollowings = (
        db.query(UserCategoryFollowing)
        .filter(UserCategoryFollowing.user_id == user_id)
        .all()
    )

    categoryStrings = []
    for userCategory in userCategoryFollowings:
        category = db.query(Category).filter(Category.id == userCategory.category_id).first()
        categoryStrings.append(category.name)

    return categoryStrings


def get_category_following(db: Session, user_id: int, category_id: int):
    return (
        db.query(UserCategoryFollowing)
        .filter(UserCategoryFollowing.user_id == user_id, UserCategoryFollowing.category_id == category_id)
        .first()
    )


def create_category_following(db: Session, user_id: int, category_id: int):
    category_following = get_category_following(db, user_id, category_id)
    if not category_following:
        category_following = UserCategoryFollowing(user_id=user_id, category_id=category_id)
        db.add(category_following)
        db.commit()
        db.refresh(category_following)
    return category_following


def get_all_keyword_following(db: Session, user_id: int):
    userKeywordFollowing = (
        db.query(UserKeywordFollowing)
        .filter(UserKeywordFollowing.user_id == user_id)
        .all()
    )

    keywordStrings = []
    for userKeyword in userKeywordFollowing:
        keyword = db.query(Keyword).filter(Keyword.id == userKeyword.keyword_id).first()
        keywordStrings.append(keyword.name)

    return keywordStrings


def get_keyword_following(db: Session, user_id: int, keyword_id: int):
    return (
        db.query(UserKeywordFollowing)
        .filter(UserKeywordFollowing.user_id == user_id, UserKeywordFollowing.keyword_id == keyword_id)
        .first()
    )


def create_keyword_following(db: Session, user_id: int, keyword_id: int):
    keyword_following = get_keyword_following(db, user_id, keyword_id)
    if not keyword_following:
        keyword_following = UserKeywordFollowing(user_id=user_id, keyword_id=keyword_id)
        db.add(keyword_following)
        db.commit()
        db.refresh(keyword_following)
    return keyword_following