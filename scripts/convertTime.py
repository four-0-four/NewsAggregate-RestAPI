import os
import aiomysql
import pytz
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

conn_params = {
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": int(os.getenv("DATABASE_PORT", "3306")),  # Convert port to integer
    "user": os.getenv("DATABASE_USERNAME", "root"),
    "password": os.getenv("DATABASE_PASSWORD", "password"),
    "db": os.getenv("DATABASE_NAME", "newsdb"),
}

async def convert_news_dates_to_utc():
    eastern = pytz.timezone('America/Toronto')

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Fetch all news articles
                await cur.execute("SELECT id, publishedDate FROM news;")
                news_articles = await cur.fetchall()

                for article in news_articles:
                    news_id, published_date = article

                    # Check if published_date is naive datetime
                    if published_date.tzinfo is None or published_date.tzinfo.utcoffset(published_date) is None:
                        # Localize the naive datetime to Eastern Time
                        local_time = eastern.localize(published_date)
                    else:
                        # Convert to Eastern Time if it's already timezone aware
                        local_time = published_date.astimezone(eastern)

                    # Convert the published date from Eastern Time to UTC
                    utc_time = local_time.astimezone(pytz.utc)

                    # Update the published date in the database
                    await cur.execute("UPDATE news SET publishedDate = %s WHERE id = %s;", (utc_time, news_id))

                await conn.commit()  # Commit all the updates

# Usage
import asyncio
asyncio.run(convert_news_dates_to_utc())
