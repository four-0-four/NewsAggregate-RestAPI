from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from app.data.userData import verify_old_password, update_user_password, get_user_by_id
from app.models.common import Keyword, Category
from app.models.user import UserCategoryFollowing, UserKeywordFollowing
from app.services.authService import create_access_token, create_refresh_token, user_to_json, new_user_to_json


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


def remove_keyword_following(db: Session, user_id: int, keyword_id: int):
    keyword_following = get_keyword_following(db, user_id, keyword_id)
    if keyword_following:
        db.delete(keyword_following)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Keyword following not found")


def remove_category_following(db: Session, user_id: int, category_id: int):
    category_following = get_category_following(db, user_id, category_id)
    if category_following:
        db.delete(category_following)
        db.commit()
    else:
        raise HTTPException(status_code=404, detail="Category following not found")


async def change_password_profile(user_id: int, old_password: str, new_password: str, confirm_password: str):
    user = await get_user_by_id(user_id)
    # Check if new_password and confirm_password match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check the old password
    if not await verify_old_password(user["email"], old_password):
        raise HTTPException(status_code=403, detail="Current password is not correct")

    # Update user's password using bcrypt hashing
    await update_user_password(user["email"], new_password)

    # Create access and refresh tokens for the user
    access_data = {
        "sub": user["username"],
        "id": user_id,
        "role": "user",
        "user": new_user_to_json(user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    # Return the access token (logging the user in)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }