from typing import Optional
import aiomysql
from app.config.database import conn_params


async def get_default_preferences() -> Optional[dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM Default_Sources")
                return await cur.fetchall()


async def delete_all_user_preferences(user_id:int) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("Delete FROM user_newsSource_preferences where userID = %s", (user_id,))
                await conn.commit()

async def insert_default_preferences_for_user(user_id: int, defaults: list) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Prepare the insert statement for multiple rows
                insert_stmt = "INSERT INTO user_newsSource_preferences (userID, CorporationID, Preference) VALUES (%s, %s, TRUE)"
                # Prepare the data tuples for insertion (user_id, corporationID) for each default source
                data_tuples = [(user_id, default['CorporationID']) for default in defaults]
                # Execute the insert statement for each default preference
                await cur.executemany(insert_stmt, data_tuples)
                await conn.commit()

async def add_user_preference(user_id: int, corporation_id: int) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                insert_stmt = "INSERT INTO user_newsSource_preferences (userID, CorporationID, Preference) VALUES (%s, %s, TRUE) ON DUPLICATE KEY UPDATE Preference = TRUE"
                await cur.execute(insert_stmt, (user_id, corporation_id))
                await conn.commit()


async def remove_user_preference(user_id: int, corporation_id: int) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                delete_stmt = "DELETE FROM user_newsSource_preferences WHERE userID = %s AND CorporationID = %s"
                await cur.execute(delete_stmt, (user_id, corporation_id))
                await conn.commit()

async def get_user_preference(user_id: int, corporation_id: int) -> bool:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                query_stmt = "SELECT * FROM user_newsSource_preferences WHERE userID = %s AND CorporationID = %s"
                await cur.execute(query_stmt, (user_id, corporation_id))
                return await cur.fetchone()