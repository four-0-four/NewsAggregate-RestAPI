from datetime import datetime

import pytest
from boto3 import Session
from app.models.news import NewsInput
from unittest.mock import create_autospec
from fastapi.testclient import TestClient
from main import app
from tests.test_authRouter import test_login_valid_user, login_test_user

client = TestClient(app)



def get_test_news():
    news_title = "Test News1: this is just a test69"
    logged_in_user = login_test_user()
    response = logged_in_user['response']
    jwt_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get(f"/news/get?news_title={news_title}", headers=headers)
    return response.json()

def test_add_news_empty_title():
    jwt_token = test_login_valid_user()
    # Arrange with empty title and valid content
    news_input = NewsInput(
        title="",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=["test", "news", "pytest"],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=123,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[
            "https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"
        ],
        categories=["sample"],
        writer_id=None
    )

    # Convert all datetime fields to strings and prepare request
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers, json=news_input_dict)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Title and content are required"

def test_add_news_empty_content():
    jwt_token = test_login_valid_user()
    # Arrange with empty title and valid content
    news_input = NewsInput(
        title="this is just a test to check everything overall",
        description="Test Description",
        content="",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=["test", "news", "pytest"],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=123,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[
            "https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"
        ],
        categories=["sample"],
        writer_id=None
    )

    # Convert all datetime fields to strings and prepare request
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers, json=news_input_dict)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Title and content are required"

def test_add_news_db():
    jwt_token = test_login_valid_user()
    response_data = get_test_news()
    print(response_data)
    if "message" in response_data and response_data["message"] == "News found successfully.":
        tst_delete_news_db()
    # Arrange
    news_input = NewsInput(
        title="Test News1: this is just a test69",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=["test", "news", "pytest"],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=5,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[
            "https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"
        ],
        categories=["sample"],
        writer_id=None
    )

    # Convert all datetime fields to strings
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers,  json=news_input_dict)

    # Assert
    assert response.json() == {"message": "News added successfully."}
    assert response.status_code == 200

    tst_get_news_db()
    tst_delete_news_db()

def test_add_news_empty_keywords():
    jwt_token = test_login_valid_user()
    # Arrange with empty title and valid content
    news_input = NewsInput(
        title="this is just a test to check everything overall",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=[],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=123,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[
            "https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"
        ],
        categories=["sample"],
        writer_id=None
    )

    # Convert all datetime fields to strings and prepare request
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers, json=news_input_dict)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Keywords lists cannot be empty"

def test_add_news_empty_categories():
    jwt_token = test_login_valid_user()
    # Arrange with empty title and valid content
    news_input = NewsInput(
        title="this is just a test to check everything overall",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=["sample"],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=123,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[
            "https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"
        ],
        categories=[],
        writer_id=None
    )

    # Convert all datetime fields to strings and prepare request
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers, json=news_input_dict)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Categories lists cannot be empty"


def test_add_news_empty_media_urls():
    jwt_token = test_login_valid_user()
    # Arrange with empty title and valid content
    news_input = NewsInput(
        title="this is just a test to check everything overall",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now().isoformat(),  # Convert to string
        language_id=1,
        isInternal=False,
        isPublished=True,
        keywords=["sample"],
        locations=["Sample Location"],  # Add a valid location
        newsCorporationID=123,  # Add a valid news corporation ID
        externalLink="https://example.com",  # Add a valid external link
        media_urls=[],
        categories=["sample"],
        writer_id=None
    )

    # Convert all datetime fields to strings and prepare request
    news_input_dict = news_input.dict()
    for key, value in news_input_dict.items():
        if isinstance(value, datetime):
            news_input_dict[key] = value.isoformat()

    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.post("/news/add", headers=headers, json=news_input_dict)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Media URLs lists cannot be empty"


def tst_get_news_db():
    news_title = "Test News1: this is just a test69"
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get(f"/news/get?news_title={news_title}", headers=headers)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "news_id" in response_data
    assert response_data["message"] == "News found successfully."
    assert isinstance(response_data["news_id"], int)

    return response_data["news_id"]


def tst_delete_news_db():
    news_title = "Test News1: this is just a test69"
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.delete(f"/news/delete?news_title={news_title}", headers=headers)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "news_id" in response_data
    assert response_data["message"] == "News deleted successfully."
    assert isinstance(response_data["news_id"], int)

    # Check if the news is deleted
    response = client.get(f"/news/get?news_title={news_title}", headers=headers)
    assert response.status_code == 409
    assert response.json() == {"detail": "News does not exists"}
