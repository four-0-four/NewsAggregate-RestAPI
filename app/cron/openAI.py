import os

from dotenv import load_dotenv
from openai import OpenAI
import json

from app.data.newsData import get_category_by_parentID

load_dotenv()

client = OpenAI(
  api_key=os.getenv('OPENAI_API_KEY'),
)
def get_news_function(categories):
    return{
        'name': 'extract_news_info',
        'description': 'Get news entities, categories, isLocal, and location',
        'parameters': {
            'type': 'object',
            'properties': {
                'entities': {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "maxLength": 10,
                    },
                    "minItems": 3,
                    "maxItems": 10,
                    "description": "Extract the primary entity such as people(full name), diseases, sports teams, scientific terms, religious groups, organizations, institutions, brands, producs, historical events, historical periods, cultural references, legal entities, social terms, economic terms, health, medicine, and major events. Avoid general or vague terms and common words.no adult words or contain adult words. should be broad yet specific to the topic, like 'COVID-19' instead of 'COVID-19 vaccine'. avoid abbreviations: use 'United States of America' instead of 'USA', and 'COVID-19' instead of 'Covid'. the entities should be full name like no 'Joe' instead of 'Joe Biden' or 'covid' instead of 'COVID-19'.",
                },
                'category': {
                    'type': 'string',
                    'enum': categories,
                    'description': 'main category of the news article. it should out of the categories listed above. it should be the one it mostly fits into. note: news about movie or tv celebrities should go to art & entertainement'
                },
                'suggestedCategory': {
                    'type': 'string',
                    'description': 'if the category above is not a good match suggest a better category here. the format category/subcategory. for example: "Politics/US Politics"'
                },
                'city': {
                    'type': 'string',
                    'description': 'city where the news took place.it should be full name and no abbreviations like "New York" instead of "NY"'
                },
                'province': {
                    'type': 'string',
                    'description': 'province where the news took place. it should be full name and no abbreviations like "British Columbia" instead of "BC"'
                },
                'country': {
                    'type': 'string',
                    'description': 'country where the news took place. it should be full name and no abbreviations like "United States of America" instead of "US"'
                }
            },
            'required': ['entities', 'category', 'subcategory', 'province', 'country']
        }
    }


# Generating response back from gpt-3.5-turbo
async def extract_news_info(news_item):
    categories = await get_category_by_parentID(0)
    category_names = [category['name'] for category in categories]
    news_custom_functions = [get_news_function(category_names)]
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': news_item.title+'\n\n'+news_item.content}],
        functions=news_custom_functions,
        function_call='auto'
    )

    # Loading the response as a JSON object
    json_response = json.loads(response.choices[0].message.function_call.arguments)
    news_item.keywords = json_response['entities']
    # Building category string
    category = json_response.get('category', '')
    news_item.categories = [category]

    # Building location string
    city = json_response.get('city', '')
    province = json_response.get('province', '')
    country = json_response.get('country', '')
    location_parts = [part for part in [city, province, country] if part is not None and part != '']
    news_item.locations = location_parts

    return news_item
