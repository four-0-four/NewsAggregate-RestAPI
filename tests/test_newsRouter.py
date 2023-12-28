from datetime import datetime

import pytest
from boto3 import Session
from app.models.news import NewsInput
from unittest.mock import create_autospec
from fastapi.testclient import TestClient
from main import app
from tests.test_authRouter import test_login_valid_user

client = TestClient(app)


def test_add_news_db():
    jwt_token = test_login_valid_user()

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
        category_id=1,
        media_urls=["https://www.thehealthy.com/wp-content/uploads/2023/04/woman-laughing-pink-background-GettyImages-1371951375-MLedit.jpg"],
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

    test_get_news_db()
    #test_delete_news_db()


def test_get_news_db():
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


def test_delete_news_db():
    news_title = "Test News1: this is just a test69"
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.delete(f"/news/delete?news_title={news_title}", headers=headers)

    # Assert
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
