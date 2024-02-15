from datetime import datetime, timedelta
from typing import List, Optional
import aiomysql

from app.config.database import conn_params


async def get_category_by_topic(topic: str) -> Optional[dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM categories WHERE name = %s;", (topic,))
                return await cur.fetchone()


async def get_keyword(keyword: str) -> Optional[dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM keywords WHERE name = %s;", (keyword,))
                return await cur.fetchone()


async def add_keyword(keyword: str):
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("INSERT INTO keywords (name) VALUES (%s);", (keyword,))
                # Commit the transaction
                await conn.commit()


async def fetch_news_by_id(news_id: int) -> Optional[List[dict]]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Optimized MySQL query
                await cur.execute("""
                    SELECT 
                        n.*, 
                        c.name as category_name, 
                        k.name as keyword_name,
                        m.fileName, 
                        ncorp.name as corporation_name,  # Changed alias to 'ncorp'
                        ncorp.logo
                    FROM news n
                    LEFT JOIN newsCategories ncat ON n.id = ncat.news_id  # Changed alias to 'ncat'
                    LEFT JOIN categories c ON ncat.category_id = c.id
                    LEFT JOIN newsKeywords nk ON n.id = nk.news_id
                    LEFT JOIN keywords k ON nk.keyword_id = k.id
                    LEFT JOIN newsMedia nm ON n.id = nm.news_id
                    LEFT JOIN media m ON nm.media_id = m.id
                    LEFT JOIN newsAffiliates na ON n.id = na.news_id
                    LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id  # Changed alias to 'ncorp'
                    WHERE n.id = %s
                """, (news_id,))

                return await cur.fetchall()


async def get_news_by_keyword(keyword_id: int, last_news_time: str, number_of_news_to_fetch: int, user_id: int) -> \
List[dict]:
    # Use current time if last_news_time is not provided
    if last_news_time is None or last_news_time == '':
        last_news_time = datetime.now()

    query = """
        SELECT 
            n.*, 
            m.fileName, 
            ncorp.name as corporation_name,
            ncorp.logo
        FROM news n
        JOIN newsKeywords nk ON n.id = nk.news_id
        LEFT JOIN newsMedia nm ON n.id = nm.news_id
        LEFT JOIN media m ON nm.media_id = m.id
        LEFT JOIN newsAffiliates na ON n.id = na.news_id
        LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
        WHERE nk.keyword_id = %s
            AND (ncorp.id NOT IN (
                   SELECT CorporationID FROM user_newsSource_preferences unp WHERE unp.userID = %s AND unp.Preference = 0))
          AND n.publishedDate < %s
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query,
                                  (keyword_id, user_id, last_news_time, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_news_by_user_following(user_id: int, last_news_time: Optional[str], number_of_news_to_fetch: int):
    # Use current time if last_news_time is not provided
    if last_news_time is None or last_news_time == '':
        last_news_time = datetime.utcnow()

    query = """
            SELECT 
                news.*,
                media.fileName,
                newsCorporations.name as corporation_name,
                newsCorporations.logo
            FROM news
            LEFT JOIN newsCategories ON news.id = newsCategories.news_id
            LEFT JOIN newsKeywords ON news.id = newsKeywords.news_id
            LEFT JOIN newsMedia ON news.id = newsMedia.news_id
            LEFT JOIN media ON newsMedia.media_id = media.id
            LEFT JOIN newsAffiliates ON news.id = newsAffiliates.news_id
            LEFT JOIN newsCorporations ON newsAffiliates.newsCorporation_id = newsCorporations.id
            WHERE news.publishedDate < %s
              AND (newsCorporations.id IN (
                   SELECT CorporationID FROM user_newsSource_preferences unp WHERE unp.userID = %s AND unp.Preference = TRUE))
              AND (newsCategories.category_id IN (
                    SELECT category_id FROM user_category_following WHERE user_id = %s)
                   OR newsKeywords.keyword_id IN (
                    SELECT keyword_id FROM user_keyword_following WHERE user_id = %s))
            ORDER BY news.publishedDate DESC
            LIMIT %s;
        """

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (last_news_time, user_id, user_id, user_id, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_news_by_category(category_id: int, last_news_time: str, number_of_news_to_fetch: int, user_id: int) -> List[dict]:
    if last_news_time is None:
        last_news_time = datetime.now()

    query = """
        SELECT 
            n.*,
            m.fileName, 
            ncorp.name as corporation_name,
            ncorp.logo
        FROM news n
        JOIN newsCategories ncat ON n.id = ncat.news_id
        LEFT JOIN newsMedia nm ON n.id = nm.news_id
        LEFT JOIN media m ON nm.media_id = m.id
        LEFT JOIN newsAffiliates na ON n.id = na.news_id
        LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
        WHERE ncat.category_id = %s
          AND (ncorp.id NOT IN (
                   SELECT CorporationID FROM user_newsSource_preferences unp WHERE unp.userID = %s AND unp.Preference = 0))
          AND n.publishedDate < %s
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (category_id, user_id, last_news_time, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_category_by_parentID(parent_category_id: int):
    query = """
    SELECT categories.* FROM categories
    JOIN newsCategories ON categories.id = newsCategories.category_id
    WHERE categories.parent_id = %s
    GROUP BY categories.id;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (parent_category_id,))
                return await cur.fetchall()