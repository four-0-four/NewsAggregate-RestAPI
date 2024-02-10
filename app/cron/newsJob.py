import requests
import json
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.data.keywordData import find_similar_keywords
from app.email.sendEmail import sendEmailInternal
from app.models.common import NewsCorporations
from app.models.news import NewsInput
from app.services.newsService import add_news_from_newsInput, get_news_by_title
from app.cron.openAI import extract_news_info
from dotenv import load_dotenv
from datetime import datetime
import os
import asyncio
from eventregistry import EventRegistry, QueryArticlesIter, ReturnInfo, ArticleInfoFlags, SourceInfoFlags

# Load environment variables
load_dotenv()

# API credentials and endpoints
newsdata_io_api_key = os.getenv('NEWS_DATA_TO_API_KEY')


number_of_news_added = 0
number_of_warnings_occured = 0
number_of_errors_occured = 0
message = ""
error_message = ""
categories_per_corporation = {}
overall_categories_count = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def write_to_json_file(filename,data):
    print("LOG: Writing news to json file...")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def fetch_news_for_corporation(corporation):
    # Assuming make_news_api_call takes category name and corporation shortName
    er = EventRegistry(apiKey='2084a034-acf9-46be-8c5f-26851ff83d3f')
    sourceUri = er.getSourceUri(corporation)
    news_list = []

    # Get the current time and 12 hours ago
    current_time = datetime.now()
    twelve_hours_ago = current_time - timedelta(hours=7)

    if(sourceUri == None or not sourceUri):
        return []

    q = QueryArticlesIter(
        sourceUri=sourceUri,
        lang="eng",
        dateStart=twelve_hours_ago,
        dateEnd=current_time
    )

    for article in q.execQuery(er, sortBy="date", returnInfo=ReturnInfo(
            sourceInfo=SourceInfoFlags(image=True)
    )):
        news_list.append(article)

    if not news_list:
        print(f"        WARNING: No news found for {corporation}...")
        return None
    else:
        print(f"        LOG: Fetched {len(news_list)} news for {corporation}...")
    return news_list

def process_news_item(news_item, news_corporation_id):
    # Convert dateTimePub to MySQL datetime format
    pub_date_str = news_item.get('dateTimePub', '')
    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%dT%H:%M:%SZ') if pub_date_str else datetime.now()

    # Get the body of the news item
    body = news_item.get('body', '')

    # Summarize the body for description
    description = body[:50] + '...' if body else ''

    news_image = news_item.get('image', '')

    keywords=[]
    location_names=[]
    categories=['all']
    media_urls=[]

    if news_image:
        media_urls.append(news_image)

    # Assuming default values for language_id, isInternal, isPublished, writer_id, and category_id
    news_data = NewsInput(
        title=news_item.get('title', ''),
        description=description,
        content=body,
        publishedDate=pub_date,
        language_id=16,
        isInternal=False,
        isPublished=False,
        keywords=keywords,
        locations=location_names,
        media_urls=media_urls,
        categories=categories,
        writer_id=None,
        newsCorporationID=news_corporation_id,
        externalLink=news_item.get('url', '')
    )

    return news_data


def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()
    elif hasattr(o, '__dict__'):
        return o.__dict__
    else:
        return str(o)

async def get_news_for_corporation_and_save(news_corporation, news_corporation_id):
    global number_of_news_added, number_of_warnings_occured, number_of_errors_occured, message, error_message
    global categories_per_corporation, overall_categories_count
    db: Session = next(get_db())
    print(f"LOG: Processing news for {news_corporation}...")
    news_list = fetch_news_for_corporation(news_corporation)
    if not news_list:
        number_of_warnings_occured += 1
        print(f"WARNING: No news found for {news_corporation}.")
        return

    local_number_of_news_added = 0
    local_number_of_warnings = 0
    local_number_of_errors = 0

    number_of_printed_news = 0

    print(f"        LOG: Processing {len(news_list)} news items for {news_corporation}...")
    for news_item in news_list:
        news_data = process_news_item(news_item, news_corporation_id)
        if not news_data:
            local_number_of_warnings += 1
            print(f"        WARNING: News item could not be processed for {news_corporation}.")
            continue

        if get_news_by_title(db, news_data.title) is not None:
            local_number_of_warnings += 1
            print(f"        WARNING: News item with title '{news_data.title}' already exists.")
            continue

        #news analysis
        '''
        print(news_data.title)
        news_data = await extract_news_info(news_data)
        if not news_data:
            local_number_of_warnings += 1
            print(f"        WARNING: News item titled '{news_data.title}' could not be analyzed.")
            continue
        '''
        try:
            response = await add_news_from_newsInput(db, news_data)
            if "message" in response and response['message'] == 'News added successfully.':
                local_number_of_news_added += 1
                number_of_news_added += 1
                print(f"        LOG: News item titled '{news_data.title}' added successfully.")

                category = news_data.categories[0]

                # Update count for this corporation
                categories_per_corporation.setdefault(news_corporation, {}).setdefault(category, 0)
                categories_per_corporation[news_corporation][category] += 1

                # Update overall count
                overall_categories_count.setdefault(category, 0)
                overall_categories_count[category] += 1
            else:
                local_number_of_warnings += 1
                print(f"        WARNING: News item titled '{news_data.title}' could not be added. Response: {response}")
        except HTTPException as http_exc:
            local_number_of_errors += 1
            number_of_errors_occured += 1
            error_detail = http_exc.detail if hasattr(http_exc, 'detail') else 'HTTP Exception without detail'
            error_message += f"Error for {news_corporation}: {error_detail}\n"
            print(
                f"        ERROR: An error occurred while adding news item titled '{news_data.title}'. Error: {error_detail}")
        except Exception as e:
            local_number_of_errors += 1
            number_of_errors_occured += 1
            error_detail = str(e) if e.args else "Unknown Error"
            error_message += f"Error for {news_corporation}: {error_detail}\n"
            print(
                f"        ERROR: An error occurred while adding news item titled '{news_data.title}'. Error: {error_detail}")

    message += f"For {news_corporation}, {local_number_of_news_added} news were added, {local_number_of_warnings} warnings happened, {local_number_of_errors} errors happened.\n"
    print(f"        LOG: {local_number_of_news_added} news items for {news_corporation} added to the database.")


def send_cron_job_summary_email():
    global message, error_message
    # Adding category count information to the email
    category_count_message = "\nCategory Summary:\n"
    for corporation, categories in categories_per_corporation.items():
        category_count_message += f"{corporation}:\n"
        for category, count in categories.items():
            category_count_message += f"    {category}: {count}\n"
    category_count_message += "\nOverall Categories Count:\n"
    for category, count in overall_categories_count.items():
        category_count_message += f"    {category}: {count}\n"

    summary_message = f"Cron Job Summary:\n{message}\n\n{category_count_message}"
    sendEmailInternal("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", 'Cron Job Summary', summary_message)

async def run_getNews_for_one_corporation(corporationName):
    db: Session = next(get_db())
    er = EventRegistry(apiKey='2084a034-acf9-46be-8c5f-26851ff83d3f')
    sourceUri = er.getSourceUri(corporationName)
    if not sourceUri:
        print(f"WARNING: News corporation {corporationName} url not found in the newsapi.ai ...")
        return
    corporation = db.query(NewsCorporations).filter(NewsCorporations.url == "https://www."+sourceUri).first()
    if not corporation:
        print(f"WARNING: News corporation {corporationName} not found in the database...")
        return
    await get_news_for_corporation_and_save(corporation.name, corporation.id)
    send_cron_job_summary_email()


async def run_news_cron_job():
    db: Session = next(get_db())
    # Retrieve all news corporations from the database
    all_corporations = db.query(NewsCorporations).all()

    for corporation in all_corporations:
        news_corporation = corporation.name
        news_corporation_id = corporation.id
        await get_news_for_corporation_and_save(news_corporation, news_corporation_id)
    send_cron_job_summary_email()



if __name__ == "__main__":
    asyncio.run(run_news_cron_job())
