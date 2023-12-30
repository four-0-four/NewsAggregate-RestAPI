from unittest import mock

import pytest
from unittest.mock import MagicMock

from app.models.common import Category
from app.services.commonService import add_news_categories_db, add_category_db, get_category, delete_last_category, \
    delete_all_categories_in_path


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

    response = add_category_db(mock_db_session, "/category/subcategory")

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

    response = add_category_db(mock_db_session, "/category/subcategory/subsubcategory")

    assert response["message"] == "Category processed successfully"
    assert len(response["category_ids"]) == 3


def test_get_category_incomplete_hierarchy(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = get_category(mock_db_session, "category/nonexistent-subcategory")

    assert response["message"] == "Category not found"


def test_get_category_single_level(mock_db_session):
    mock_single_category = Category(id=1, name="category")
    mock_db_session.query(Category).filter.return_value.first.return_value = mock_single_category

    response = get_category(mock_db_session, "category")

    assert response["message"] == "Got category successfully"
    assert response["category"].id == 1


def test_delete_last_category_success(mock_db_session):
    mock_category = Category(id=1, name="category")
    mock_db_session.query(Category).filter.return_value.first.return_value = mock_category

    response = delete_last_category(mock_db_session, "category")

    mock_db_session.delete.assert_called_with(mock_category)
    mock_db_session.commit.assert_called()
    assert response["message"] == "Category deleted successfully"


def test_delete_last_category_not_found(mock_db_session):
    mock_db_session.query(Category).filter.return_value.first.return_value = None

    response = delete_last_category(mock_db_session, "nonexistent-category")

    assert response["message"] == "Category not found"


def test_delete_all_categories_in_path_success(mock_db_session):
    mock_category = Category(id=1, name="category")
    mock_subcategory = Category(id=2, name="subcategory", parent_id=1)

    # Mock the query object's first method to return mock_category and mock_subcategory
    mock_query = mock_db_session.query(Category)
    mock_query.filter.side_effect = [mock.MagicMock(first=mock.MagicMock(return_value=mock_category)),
                                     mock.MagicMock(first=mock.MagicMock(return_value=mock_subcategory))]

    response = delete_all_categories_in_path(mock_db_session, "category/subcategory")

    assert mock_db_session.delete.call_count == 2
    mock_db_session.commit.assert_called()
    assert response["message"] == "All categories in path deleted successfully"


def test_delete_all_categories_in_path_not_found(mock_db_session):
    mock_category = Category(id=1, name="category")

    # Mock the query object's first method to return mock_category and then None
    mock_query = mock_db_session.query(Category)
    mock_query.filter.side_effect = [mock.MagicMock(first=mock.MagicMock(return_value=mock_category)),
                                     mock.MagicMock(first=mock.MagicMock(return_value=None))]

    response = delete_all_categories_in_path(mock_db_session, "category/nonexistent-subcategory")

    assert response["message"] == "Category 'nonexistent-subcategory' not found in path"



