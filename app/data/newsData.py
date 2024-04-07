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


async def get_entity(entity: str) -> Optional[dict]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM entities WHERE name = %s;", (entity,))
                return await cur.fetchone()


async def create_category_following(user_id: int, category_id: int) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    # Execute the SQL command
                    await cur.execute("INSERT INTO userTopicFollowing (userID, topicID, topicType) VALUES (%s, %s, 'CATEGORY');", (user_id, category_id))
                    await conn.commit()
                except Exception as e:
                    # Catch any other exceptions that may occur
                    await conn.rollback()
                
                
async def create_entity_following(user_id: int, entity_id: int) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("INSERT INTO userTopicFollowing (userID, topicID, topicType) VALUES (%s, %s, 'ENTITY');", (user_id, entity_id,))
                # Commit the transaction
                await conn.commit()


async def add_entity(entity: str, type: str) -> None:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("INSERT INTO entities (name, type) VALUES (%s, %s);", (entity,type, ))
                # Commit the transaction
                await conn.commit()


async def fetch_news_by_id(news_id: int) -> Optional[List[dict]]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Adjusted MySQL query
                await cur.execute("""
                    SELECT 
                        news.id,
                        news.title,
                        news.publishedDate,
                        news.ProcessedForIdentity,
                        news.corporationID,
                        news.corporationName AS 'from',
                        news.corporationLogo AS 'fromImage',
                        news.mainImage AS media,
                        news.longSummary,
                        news.newsExternalLink AS externalLink,
                        null as isBookmarked
                    FROM news
                    WHERE news.id = %s
                """, (news_id,))

                return await cur.fetchone()


async def fetch_news_by_id_authenticated(news_id: int, user_id: int) -> Optional[List[dict]]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Adjusted MySQL query
                await cur.execute("""
                    SELECT 
                        news.id,
                        news.title,
                        news.publishedDate,
                        news.ProcessedForIdentity,
                        news.corporationID,
                        news.corporationName AS 'from',
                        news.corporationLogo AS 'fromImage',
                        news.mainImage AS media,
                        news.longSummary,
                        news.newsExternalLink AS externalLink,
                        CASE 
                            WHEN bn.newsID IS NOT NULL THEN TRUE
                            ELSE FALSE
                        END as isBookmarked
                    FROM news
                    LEFT JOIN bookmarked_news bn ON news.id = bn.newsID AND bn.userID = %s
                    WHERE news.id = %s
                """, (user_id, news_id,))

                return await cur.fetchone()


async def get_news_by_entity(entity_id: int, last_news_time: str, number_of_news_to_fetch: int, user_id: int) -> \
List[dict]:
    # Use current time if last_news_time is not provided
    if last_news_time is None or last_news_time == '':
        last_news_time = datetime.now()

    query = """
        SELECT 
            n.id,
            n.title,
            n.publishedDate,
            n.ProcessedForIdentity,
            n.corporationID,
            n.corporationName AS 'from',
            n.corporationLogo AS 'fromImage',
            n.mainImage AS media,
            n.newsExternalLink AS externalLink,
            CASE 
                WHEN bn.newsID IS NOT NULL THEN TRUE
                ELSE FALSE
            END as isBookmarked
        FROM news n
        LEFT JOIN newsTopic ON n.id = newsTopic.newsID
        LEFT JOIN bookmarked_news bn ON n.id = bn.newsID AND bn.userID = %s
        WHERE 
            n.publishedDate < %s
            AND n.summarized = 1
            AND n.ProcessedForIdentity = 1
            AND NOT EXISTS (
                SELECT 1
                FROM userNewsSourcePreferences
                WHERE userID = %s
                    AND userNewsSourcePreferences.CorporationID = n.corporationID
                    AND Preference = 0
            )
            AND newsTopic.topicID = %s AND newsTopic.topicType = 'ENTITY'
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id, last_news_time, user_id, entity_id, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_news_by_user_following(user_id: int, last_news_time: Optional[str], number_of_news_to_fetch: int):
    # Use current time if last_news_time is not provided
    if last_news_time is None or last_news_time == '':
        last_news_time = datetime.utcnow()

    query = """
        SELECT
    news.id,
    news.title,
    news.publishedDate,
    news.ProcessedForIdentity,
    news.corporationID,
    news.corporationName AS 'from',
    news.corporationLogo AS 'fromImage',
    news.mainImage AS media,
    news.newsExternalLink AS externalLink,
    CASE
        WHEN bookmarked_news.newsID IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS isBookmarked
    FROM
        news
    LEFT JOIN newsTopic ON news.id = newsTopic.newsID
    LEFT JOIN bookmarked_news ON news.id = bookmarked_news.newsID AND bookmarked_news.userID = %s
    WHERE
        news.publishedDate < %s
        AND news.summarized = 1
        AND news.ProcessedForIdentity = 1
        AND EXISTS (
            SELECT 1
            FROM userNewsSourcePreferences
            WHERE userID = %s
                AND userNewsSourcePreferences.CorporationID = news.corporationID
                AND Preference = 1
        )
        AND( newsTopic.topicID IN (
                SELECT topicID
                FROM userTopicFollowing
                WHERE userID = %s AND topicType = 'ENTITY'
            ) OR newsTopic.topicID IN (
                SELECT topicID
                FROM userTopicFollowing
                WHERE userID = %s AND topicType = 'CATEGORY'
            )
        )
    ORDER BY
        news.publishedDate DESC
    LIMIT %s;
    """

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id, last_news_time, user_id, user_id, user_id, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_news_by_category(category_id: int, last_news_time: str, number_of_news_to_fetch: int, user_id: int) -> List[dict]:
    if last_news_time is None:
        last_news_time = datetime.now()

    query = """
        SELECT 
            n.id,
            n.title,
            n.publishedDate,
            n.ProcessedForIdentity,
            n.corporationID,
            n.corporationName AS 'from',
            n.corporationLogo AS 'fromImage',
            n.mainImage AS media,
            n.newsExternalLink AS externalLink,
            CASE 
                WHEN bn.newsID IS NOT NULL THEN TRUE
                ELSE FALSE
            END as isBookmarked
        FROM news n
        LEFT JOIN newsTopic ON n.id = newsTopic.newsID
        LEFT JOIN bookmarked_news bn ON n.id = bn.newsID AND bn.userID = %s
        WHERE 
            n.publishedDate < %s
            AND n.summarized = 1
            AND n.ProcessedForIdentity = 1
            AND NOT EXISTS (
                SELECT 1
                FROM userNewsSourcePreferences
                WHERE userID = %s
                    AND userNewsSourcePreferences.CorporationID = n.corporationID
                    AND Preference = 0
            )
            AND newsTopic.topicID = %s AND newsTopic.topicType = 'CATEGORY'
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id, last_news_time, user_id, category_id, number_of_news_to_fetch))
                return await cur.fetchall()


async def get_category_by_parentID(parent_category_id: int):
    query = """
    SELECT categories.* FROM categories
    WHERE categories.parent_id = %s
    GROUP BY categories.id;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (parent_category_id,))
                return await cur.fetchall()
            
            
########################BOOKMARKS########################

async def check_news_exists_by_id(news_id: int) -> bool:
    query = "SELECT COUNT(*) FROM news WHERE id = %s;"

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (news_id,))
                result = await cur.fetchone()
                return result[0] > 0


async def add_news_to_bookmark(user_id: int, news_id: int):
    query = """
    INSERT INTO bookmarked_news (userID, newsID) VALUES (%s, %s);
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id, news_id))
                await conn.commit()

async def remove_news_from_bookmark(user_id: int, news_id: int):
    query = """
    DELETE FROM bookmarked_news WHERE userID = %s AND newsID = %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_id, news_id))
                await conn.commit()

async def get_all_bookmarks_for_user(user_id: int):
    query = """
        SELECT 
            news.*,
            media.fileName,
            newsCorporations.name as corporation_name,
            newsCorporations.logo,
            TRUE as isBookmarked
        FROM news
        LEFT JOIN newsMedia ON news.id = newsMedia.news_id
        LEFT JOIN media ON newsMedia.media_id = media.id
        LEFT JOIN newsAffiliates ON news.id = newsAffiliates.news_id
        LEFT JOIN newsCorporations ON newsAffiliates.newsCorporation_id = newsCorporations.id
        WHERE news.id IN (
            SELECT newsID FROM bookmarked_news WHERE userID = %s
        );
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id,))
                return await cur.fetchall()