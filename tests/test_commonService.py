import pytest
from unittest.mock import MagicMock

from app.models.common import Category
from app.services.commonService import add_news_categories_db, add_category_db, get_category


# Mock session object
@pytest.fixture
def mock_db_session():
    # This is a mock session object
    session = MagicMock()
    return session


# Test for add_news_categories_db
def test_add_news_categories_db(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = add_news_categories_db(mock_db_session, "/category/subcategory", 1)

    assert response["message"] == "Category processed successfully"
    assert isinstance(response["category_ids"], list)


# Test for add_category_db
def test_add_category_db(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = add_category_db(mock_db_session, "/category/subcategory", 1)

    assert response["message"] == "Category processed successfully"
    assert isinstance(response["category_ids"], list)


# Test for get_category
def test_get_category(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = get_category(mock_db_session, "/category/subcategory")

    assert response["message"] == "Category not found"

    mock_db_session.query(Category).filter.return_value.first.return_value = Category(id=1, name="subcategory")

    response = get_category(mock_db_session, "/category/subcategory")

    assert response["message"] == "Got category successfully"
    assert response["category"].id == 1
    assert response["category"].name == "subcategory"


def test_add_news_categories_db_existing_category(mock_db_session):
    mock_existing_category = Category(id=1, name="category")
    mock_db_session.query(Category).filter.return_value.first.return_value = mock_existing_category

    response = add_news_categories_db(mock_db_session, "/category", 1)

    assert response["message"] == "Category processed successfully"
    assert 1 in response["category_ids"]


def test_add_category_db_deep_hierarchy(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.side_effect = [None, None, Category(id=2, name="subcategory")]

    response = add_category_db(mock_db_session, "/category/subcategory/subsubcategory", 1)

    assert response["message"] == "Category processed successfully"
    assert len(response["category_ids"]) == 3


def test_get_category_incomplete_hierarchy(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = get_category(mock_db_session, "/category/nonexistent_subcategory")

    assert response["message"] == "Category not found"


def test_get_category_single_level(mock_db_session):
    mock_single_category = Category(id=1, name="category")
    mock_db_session.query(Category).filter.return_value.first.return_value = mock_single_category

    response = get_category(mock_db_session, "category")

    assert response["message"] == "Got category successfully"
    assert response["category"].id == 1
