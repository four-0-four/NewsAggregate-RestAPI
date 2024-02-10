import json

from newsplease import NewsPlease
articles = []

def extract_info(url:str):
    article = NewsPlease.from_url(url)
    return {
        'title': article.title,
        'text': article.maintext,
        'image': "",
        'date': article.date_publish
    }


article= extract_info('https://www.cbc.ca/news/politics/danielle-smith-liberal-government-trade-barbs-trans-1.7105175')

# Check if the date includes timezone information
if article['date'] is not None:
    if article['date'].tzinfo is not None and article['date'].tzinfo.utcoffset(article['date']) is not None:
        timezone_info = f"Timezone: {article['date'].tzinfo}"
    else:
        timezone_info = "Timezone information is not available."
else:
    timezone_info = "Publication date is not available."


print(f"Title: {article['title']} Date: {article['date']} {timezone_info}")
