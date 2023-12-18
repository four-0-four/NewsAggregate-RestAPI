from datetime import datetime

import pytest
from boto3 import Session
from app.models.news import NewsInput
from unittest.mock import create_autospec
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

async def test_add_news_db():
    # Arrange
    news_input = NewsInput(
        title="Test News",
        description="Test Description",
        content="This is a test content for the news.",
        publishedDate=datetime.now(),
        language_id=1,  # Assuming 1 is a valid language ID in your database
        isInternal=False,
        isPublished=True,
        writer_id=1,  # Assuming 1 is a valid writer ID in your database
        keywords=["test", "news", "pytest"]
    )

    # Act
    response = client.post("/news/add", json=news_input.dict())

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "News added successfully."}


async def get_news_db(news_title):
    # Act
    response = client.post(f"/news/add?news_title={news_title}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "News added successfully."}
