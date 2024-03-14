import aiomysql

from app.config.database import conn_params


async def find_similar_entities(input_entity):
    similar_entities = []

    # Breaking down the input entity for better accuracy
    combined_entities = set()  # Using a set to automatically handle duplicates

    for entity in input_entity:
        # Split each entity into words, convert to lowercase, and add to the set
        combined_entities.update(word.lower() for word in entity.split())
   
    search_terms = list(combined_entities)
    
    # SQL Query
    query = "SELECT name FROM entities WHERE name LIKE %s"

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for term in search_terms:
                    like_term = f"%{term}%"
                    await cur.execute(query, (like_term,))
                    results = await cur.fetchall()
                    for result in results:
                        if result[0] not in similar_entities:
                            similar_entities.append(result[0])

    return similar_entities