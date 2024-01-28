from typing import Optional

import aiomysql

from app.config.database import conn_params
from app.config.dependencies import bcrypt_context


async def check_username_in_db(username: str) -> bool:
    query = "SELECT EXISTS(SELECT 1 FROM users WHERE username = %s)"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (username,))
                exists = await cur.fetchone()
                return exists[0]

async def update_username_in_db(user_id: int, username: str):
    query = "UPDATE users SET username = %s WHERE id = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (username, user_id))
                await conn.commit()

async def update_first_name_in_db(user_id: int, first_name: str):
    query = "UPDATE users SET first_name = %s WHERE id = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (first_name, user_id))
                await conn.commit()

async def update_last_name_in_db(user_id: int, last_name: str):
    query = "UPDATE users SET last_name = %s WHERE id = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (last_name, user_id))
                await conn.commit()


async def get_user_by_id(user_id: int) -> Optional[dict]:
    query = "SELECT username, email, first_name, last_name, is_active FROM users WHERE id = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id,))
                user = await cur.fetchone()
                return user if user else None


async def verify_old_password(email: str, old_password: str) -> bool:
    query = "SELECT hashed_password FROM users WHERE email = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (email,))
                result = await cur.fetchone()
                if result:
                    # Verify the password (assuming bcrypt_context is available for password checking)
                    return bcrypt_context.verify(old_password, result[0])
                return False

async def update_user_password(email: str, new_password: str):
    hashed_password = bcrypt_context.hash(new_password)
    query = "UPDATE users SET hashed_password = %s WHERE email = %s"
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (hashed_password, email))
                await conn.commit()