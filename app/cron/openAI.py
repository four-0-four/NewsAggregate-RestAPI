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
                'category': {
                    'type': 'string',
                    'enum': categories,
                    'description': 'main category of the news article. it should out of the categories listed above. it should be the one it mostly fits into. note: news about movie or tv celebrities should go to art & entertainement'
                },
            },
            'required': ['category']
        }
    }


# Generating response back from gpt-3.5-turbo
async def extract_news_info(news_item):
    categories = await get_category_by_parentID(0)
    category_names = [category['name'] for category in categories]
    news_custom_functions = [get_news_function(category_names)]
    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': "news title: '"+news_item.title+"'\n\n"+"news body: '"+news_item.content[:12000]+"'"}],
        functions=news_custom_functions,
        function_call='auto'
    )

    # Loading the response as a JSON object
    json_response = {}
    if response.choices and response.choices[0].message.function_call:
        json_response = json.loads(response.choices[0].message.function_call.arguments)
    else:
        return None

    # Building category string
    category = json_response.get('category', '')
    news_item.categories = [category]
    print(category)
    while category not in categories:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user',
                       'content': "choose a chategory for the following news based on one of these categories:"+", ".join(categories)+"\n\n"+"news title: '" + news_item.title + "'\n\n" + "news body: '" + news_item.content[
                                                                                                 :12000] + "'"}],
            functions=news_custom_functions,
            function_call='auto'
        )
        json_response = {}
        if response.choices and response.choices[0].message.function_call:
            json_response = json.loads(response.choices[0].message.function_call.arguments)
        else:
            return None
        category = json_response.get('category', '')
        print(category)
        news_item.categories = [category]


    return news_item
