import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.email.sendEmail import sendEmailInternal
from app.models.common import NewsCorporations
from app.models.news import NewsInput
from app.services.newsService import add_news_from_newsInput, get_news_by_title
from dotenv import load_dotenv
import os
from app.services.authService import authenticate_user
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
    twelve_hours_ago = current_time - timedelta(hours=12)

    q = QueryArticlesIter(
        sourceUri=sourceUri,
        lang="eng",
        dateStart=twelve_hours_ago,
        dateEnd=current_time
    )

    for article in q.execQuery(er, sortBy="date", returnInfo=ReturnInfo(
            articleInfo=ArticleInfoFlags(concepts=True, categories=True, location=True),
            sourceInfo=SourceInfoFlags(location=True, image=True)
    )):
        news_list.append(article)

    if not news_list:
        print(f"        WARNING: No news found for {corporation}...")
        return None
    else:
        print(f"        LOG: Fetched {len(news_list)} news for {corporation}...")
    return news_list


def get_categories(news_item):
    categories = news_item.get('categories', [])
    extracted_categories = []

    for cat in categories:
        # Check if the URI contains '/'
        if '/' in cat['uri']:
            # Split the URI into parts
            parts = cat['uri'].split('/')
            # Remove the first part and reassemble the rest
            cleaned_uri = '/'.join(parts[1:])
            # Add to the extracted categories
            extracted_categories.append(cleaned_uri)

    return extracted_categories


def get_keywords(news_item):
    # Extract the list of concepts from the news item. If there are no concepts,
    # an empty list is used as a default.
    concepts = news_item.get('concepts', [])

    # Initialize an empty list to hold the extracted keywords.
    keywords = []

    # Loop through each concept in the concepts list.
    for concept in concepts:
        # Check if the concept has a 'label' key and if 'eng' key exists in the 'label'.
        if concept["score"] >= 3 and 'label' in concept and 'eng' in concept['label']:
            # Extract the English label and add it to the keywords list.
            keywords.append(concept['label']['eng'])

    # Return the list of extracted keywords.
    return keywords


def extract_location_names(news_item):
    # Extract the list of concepts from the news item. If there are no concepts,
    # an empty list is used as a default.
    concepts = news_item.get('concepts', [])


    location_names = []

    for concept in concepts:
        # Check if the concept type is 'loc' and if 'label' key exists with 'eng' subkey
        if concept.get('type') == 'loc' and 'label' in concept and 'eng' in concept['label']:
            # Extract the English label
            loc_label = concept['label']['eng']

            # Split the label by comma and strip whitespace
            locations = [loc.strip() for loc in loc_label.split(',')]

            # Extend the location_names list with these locations
            location_names.extend(locations)

    return location_names

def process_news_item(news_item, news_corporation_id):
    # Convert dateTimePub to MySQL datetime format
    pub_date_str = news_item.get('dateTimePub', '')
    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%dT%H:%M:%SZ') if pub_date_str else datetime.now()

    # get keywords
    keywords = get_keywords(news_item)

    # get categories
    categories = get_categories(news_item)

    #get location names
    location_names = extract_location_names(news_item)

    # Get the body of the news item
    body = news_item.get('body', '')

    # Summarize the body for description
    description = body[:50] + '...' if body else ''

    news_image = news_item.get('image', '')
    if not news_image:
        return False

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
        media_urls=[news_image],
        categories=categories,
        writer_id=None,
        newsCorporationID=news_corporation_id,
        externalLink=news_item.get('url', '')
    )

    return news_data


def get_news_for_corporation_and_save(news_corporation, news_corporation_id):
    global number_of_news_added, number_of_warnings_occured, number_of_errors_occured, message, error_message
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

        try:
            response = add_news_from_newsInput(db, news_data)
            if "message" in response and response['message'] == 'News added successfully.':
                local_number_of_news_added += 1
                number_of_news_added += 1
                print(f"        LOG: News item titled '{news_data.title}' added successfully.")
            else:
                local_number_of_warnings += 1
                print(f"        WARNING: News item titled '{news_data.title}' could not be added. Response: {response}")
        except Exception as e:
            local_number_of_errors += 1
            number_of_errors_occured += 1
            error_message += f"Error for {news_corporation}: {e}\n"
            print(f"        ERROR: An error occurred while adding news item titled '{news_data.title}'. Error: {e}")

    message += f"For {news_corporation}, {local_number_of_news_added} news were added, {local_number_of_warnings} warnings happened, {local_number_of_errors} errors happened.\n"
    print(f"        LOG: {local_number_of_news_added} news items for {news_corporation} added to the database.")


def send_cron_job_summary_email():
    global message, error_message
    summary_message = f"Cron Job Summary:\n{message}\nErrors:\n{error_message}"
    sendEmailInternal("Farabix Support <admin@farabix.com>", "msina.raf@gmail.com", 'Cron Job Summary', summary_message)


def run_getNews_for_one_corporation(corporationName):
    db: Session = next(get_db())
    er = EventRegistry(apiKey='2084a034-acf9-46be-8c5f-26851ff83d3f')
    sourceUri = er.getSourceUri(corporationName)
    print(sourceUri)
    corporation = db.query(NewsCorporations).filter(NewsCorporations.url == "https://www." + sourceUri).first()
    if not corporation:
        print(f"WARNING: News corporation {corporationName} not found in the database...")
        return
    get_news_for_corporation_and_save(corporation.name, corporation.id)


def run_news_cron_job():
    db: Session = next(get_db())
    # Retrieve all news corporations from the database
    all_corporations = db.query(NewsCorporations).all()

    for corporation in all_corporations:
        news_corporation = corporation.name
        news_corporation_id = corporation.id
        get_news_for_corporation_and_save(news_corporation, news_corporation_id)



if __name__ == "__main__":
    run_news_cron_job()
