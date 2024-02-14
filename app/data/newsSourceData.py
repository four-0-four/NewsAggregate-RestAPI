from typing import Optional
import aiomysql
from app.config.database import conn_params

async def get_all_news_sources_db() -> [dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                query_stmt = "SELECT * FROM newsCorporations"
                await cur.execute(query_stmt)
                return await cur.fetchall()

async def get_user_all_newsSource_preferences(user_id: int) -> [dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                query_stmt = "SELECT * FROM newsCorporations where id in (SELECT CorporationID FROM user_newsSource_preferences WHERE userID = %s AND Preference = 1)"
                await cur.execute(query_stmt, (user_id))
                return await cur.fetchall()