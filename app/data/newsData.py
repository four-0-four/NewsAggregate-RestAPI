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
                        n.*, 
                        c.name as category_name, 
                        k.name as entity_name,
                        m.fileName, 
                        ncorp.name as corporation_name,
                        ncorp.logo,
                        na.externalLink,
                        null as isBookmarked
                    FROM news n
                    LEFT JOIN newsCategories ncat ON n.id = ncat.news_id
                    LEFT JOIN categories c ON ncat.category_id = c.id
                    LEFT JOIN newsEntities nk ON n.id = nk.news_id
                    LEFT JOIN entities k ON nk.entity_id = k.id
                    LEFT JOIN newsMedia nm ON n.id = nm.news_id
                    LEFT JOIN media m ON nm.media_id = m.id
                    LEFT JOIN newsAffiliates na ON n.id = na.news_id
                    LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
                    WHERE n.id = %s
                """, (news_id,))

                return await cur.fetchall()



async def fetch_news_by_id_authenticated(news_id: int, user_id: int) -> Optional[List[dict]]:
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Adjusted MySQL query
                await cur.execute("""
                    SELECT 
                        n.*, 
                        c.name as category_name, 
                        k.name as entity_name,
                        m.fileName, 
                        ncorp.name as corporation_name,
                        ncorp.logo,
                        na.externalLink,
                        CASE 
                            WHEN bn.newsID IS NOT NULL THEN TRUE
                            ELSE FALSE
                        END as isBookmarked
                    FROM news n
                    LEFT JOIN newsCategories ncat ON n.id = ncat.news_id
                    LEFT JOIN categories c ON ncat.category_id = c.id
                    LEFT JOIN newsEntities nk ON n.id = nk.news_id
                    LEFT JOIN entities k ON nk.entity_id = k.id
                    LEFT JOIN newsMedia nm ON n.id = nm.news_id
                    LEFT JOIN media m ON nm.media_id = m.id
                    LEFT JOIN newsAffiliates na ON n.id = na.news_id
                    LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
                    LEFT JOIN bookmarked_news bn ON n.id = bn.newsID AND bn.userID = %s
                    WHERE n.id = %s
                """, (user_id, news_id,))

                return await cur.fetchall()


async def get_news_by_entity(entity_id: int, last_news_time: str, number_of_news_to_fetch: int, user_id: int) -> \
List[dict]:
    # Use current time if last_news_time is not provided
    if last_news_time is None or last_news_time == '':
        last_news_time = datetime.now()

    query = """
        SELECT 
            n.*, 
            m.fileName, 
            ncorp.name as corporation_name,
            ncorp.logo,
            CASE 
                WHEN bn.newsID IS NOT NULL THEN TRUE
                ELSE FALSE
            END as isBookmarked
        FROM news n
        JOIN newsEntities nk ON n.id = nk.news_id
        LEFT JOIN newsMedia nm ON n.id = nm.news_id
        LEFT JOIN media m ON nm.media_id = m.id
        LEFT JOIN newsAffiliates na ON n.id = na.news_id
        LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
        LEFT JOIN bookmarked_news bn ON n.id = bn.newsID AND bn.userID = %s
        WHERE nk.entity_id = %s
            AND (ncorp.id NOT IN (
                   SELECT CorporationID FROM user_newsSource_preferences WHERE userID = %s AND unp.Preference = 0))
          AND n.publishedDate < %s
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query,
                                  (user_id, entity_id, user_id, last_news_time, number_of_news_to_fetch))
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
            newsCorporations.logo,
            CASE 
                WHEN bookmarked_news.newsID IS NOT NULL THEN TRUE
                ELSE FALSE
            END as isBookmarked
        FROM news
        LEFT JOIN newsCategories ON news.id = newsCategories.news_id
        LEFT JOIN newsEntities ON news.id = newsEntities.news_id
        LEFT JOIN newsMedia ON news.id = newsMedia.news_id
        LEFT JOIN media ON newsMedia.media_id = media.id
        LEFT JOIN newsAffiliates ON news.id = newsAffiliates.news_id
        LEFT JOIN newsCorporations ON newsAffiliates.newsCorporation_id = newsCorporations.id
        LEFT JOIN bookmarked_news ON news.id = bookmarked_news.newsID AND bookmarked_news.userID = %s
        WHERE news.publishedDate < %s
          AND (newsCorporations.id IN (
               SELECT CorporationID FROM user_newsSource_preferences WHERE userID = %s AND Preference = TRUE))
          AND (newsCategories.category_id IN (
                SELECT category_id FROM user_category_following WHERE user_id = %s)
               OR newsEntities.entity_id IN (
                SELECT entity_id FROM user_entity_following WHERE user_id = %s))
        ORDER BY news.publishedDate DESC
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
            n.*,
            m.fileName, 
            ncorp.name as corporation_name,
            ncorp.logo,
            CASE 
                WHEN bn.newsID IS NOT NULL THEN TRUE
                ELSE FALSE
            END as isBookmarked
        FROM news n
        JOIN newsCategories ncat ON n.id = ncat.news_id
        LEFT JOIN newsMedia nm ON n.id = nm.news_id
        LEFT JOIN media m ON nm.media_id = m.id
        LEFT JOIN newsAffiliates na ON n.id = na.news_id
        LEFT JOIN newsCorporations ncorp ON na.newsCorporation_id = ncorp.id
        LEFT JOIN bookmarked_news bn ON n.id = bn.newsID AND bn.userID = %s
        WHERE ncat.category_id = %s
          AND (ncorp.id NOT IN (
                   SELECT CorporationID FROM user_newsSource_preferences WHERE userID = %s AND Preference = 0))
          AND n.publishedDate < %s
        ORDER BY n.publishedDate DESC
        LIMIT %s;
    """
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, (user_id, category_id, user_id, last_news_time, number_of_news_to_fetch))
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