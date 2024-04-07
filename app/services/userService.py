from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from app.data.userData import verify_old_password, update_user_password, get_user_by_id
from aiomysql import create_pool, DictCursor
from app.services.authService import create_access_token, create_refresh_token, user_to_json, new_user_to_json
from app.config.database import conn_params



async def get_all_category_following(user_id: int):
    async with create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    "SELECT name FROM categories INNER JOIN userTopicFollowing ON categories.id = userTopicFollowing.topicID WHERE userTopicFollowing.userID = %s AND userTopicFollowing.topicType = 'CATEGORY'",
                    (user_id,)
                )
                categories = await cur.fetchall()
                category_strings = [category['name'] for category in categories]
                return category_strings


async def get_all_entity_following(user_id: int):
    async with create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    "SELECT name FROM entities INNER JOIN userTopicFollowing ON entities.id = userTopicFollowing.topicID WHERE userTopicFollowing.userID = %s AND userTopicFollowing.topicType = 'ENTITY'",
                    (user_id,)
                )
                entities = await cur.fetchall()
                entity_strings = [entity['name'] for entity in entities]
                return entity_strings


async def remove_entity_following(user_id: int, entity_id: int):
    async with create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM userTopicFollowing WHERE userID = %s AND topicID = %s AND topicType = 'ENTITY'",
                    (user_id, entity_id)
                )
                affected = cur.rowcount
                await conn.commit()
                if affected == 0:
                    raise HTTPException(status_code=404, detail="Entity following not found")

async def remove_category_following(user_id: int, category_id: int):
    async with create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM userTopicFollowing WHERE userID = %s AND topicID = %s AND topicType = 'CATEGORY'",
                    (user_id, category_id)
                )
                affected = cur.rowcount
                await conn.commit()
                if affected == 0:
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