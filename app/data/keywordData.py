import aiomysql

from app.config.database import conn_params


async def find_similar_keywords(input_keyword):
    similar_keywords = []

    # Breaking down the input keyword for better accuracy
    combined_keywords = set()  # Using a set to automatically handle duplicates

    for keyword in input_keyword:
        # Split each keyword into words, convert to lowercase, and add to the set
        combined_keywords.update(word.lower() for word in keyword.split())
   
    search_terms = list(combined_keywords)
    
    # SQL Query
    query = "SELECT name FROM keywords WHERE name LIKE %s"

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for term in search_terms:
                    like_term = f"%{term}%"
                    await cur.execute(query, (like_term,))
                    results = await cur.fetchall()
                    for result in results:
                        if result[0] not in similar_keywords:
                            similar_keywords.append(result[0])

    return similar_keywords