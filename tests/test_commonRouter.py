# important to add
import json
import sys
import os
from pydantic import ValidationError
sys.path.append(os.getcwd())
from fastapi.testclient import TestClient
from main import app
from tests.test_authRouter import test_login_valid_user
import requests

client = TestClient(app)


def test_get_category_empty():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.get("/common/category", params={"category": ""}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_add_category_empty():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.post("/common/category", params={"category": ""}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_delete_category_empty():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.delete("/common/category", params={"category": ""}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_get_category_consecutive_slashes():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.get("/common/category", params={"category": "technology//gadgets"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_add_category_consecutive_slashes():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.post("/common/category", params={"category": "sports//test_sport"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_delete_category_consecutive_slashes():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.delete("/common/category", params={"category": "sports//test_sport"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_get_category_illegal_characters():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.get("/common/category", params={"category": "tech$@!nology"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_add_category_illegal_characters():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.post("/common/category", params={"category": "sport@!test_sport"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_delete_category_illegal_characters():
    jwt_token = test_login_valid_user()
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = client.delete("/common/category", params={"category": "sport@!test_sport"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid category path"}


def test_get_category_success_one_category():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "technology"}, headers=headers)

    # Assert
    assert response.status_code == 200
    assert "category" in response.json()
    assert response.json()["category"]["name"] == "technology"


def test_get_category_success_2ndLevel_sub_category():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "sports/Football"}, headers=headers)

    # Assert
    assert response.status_code == 200
    assert "category" in response.json()
    assert response.json()["category"]["name"] == "Football"

def test_get_category_failure_one_category():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "non-existent-category"}, headers=headers)

    # Assert
    assert response.status_code == 404  # Assuming your API returns 404 for not found
    assert response.json() == {"detail" : "Category not found"}


def test_get_category_failure_2ndLevel_category():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "sports/non-existent-category"}, headers=headers)

    # Assert
    assert response.status_code == 404  # Assuming your API returns 404 for not found
    assert response.json() == {"detail" : "Category not found"}


def test_get_category_failure_parent_2ndLevel_category():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "non-existent-category/soccer"}, headers=headers)

    # Assert
    assert response.status_code == 404  # Assuming your API returns 404 for not found
    assert response.json() == {"detail" : "Category not found"}

def test_add_category_success():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act
    response = client.get("/common/category", params={"category": "sports/test-sport"}, headers=headers)
    if response.status_code == 200 and "category" in response.json():
        client.delete("/common/category", params={"category": "sports/test-sport"}, headers=headers)

    # Act
    response = client.post("/common/category", params={"category": "sports/test-sport"}, headers=headers)

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Category processed successfully"
    assert len(response.json()["category_ids"]) > 0

    client.delete("/common/category", params={"category": "sports/test-sport"}, headers=headers)


def test_upload_file():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Arrange for file upload
    test_file_url = "https://farabix-resources.nyc3.cdn.digitaloceanspaces.com/unittests/test_file.jpg"

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act - Get the file content from the URL and upload the file
    response = requests.get(test_file_url)
    file_content = response.content
    file_name = test_file_url.split('/')[-1]

    upload_response = client.post("/common/file/upload",
                                  headers=headers,
                                  files={"file": (file_name, file_content, "image/jpg")},
                                  data={"file_type": "website"})

    # Assert - Check upload success
    assert upload_response.status_code == 200
    assert "full_file_path" in upload_response.json()

    # Get the uploaded file name for deletion
    full_file_path = upload_response.json()["full_file_path"]

    return full_file_path, jwt_token

def test_upload_invalid_file_type():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Arrange for file uploads
    test_file_url = "https://farabix-resources.nyc3.cdn.digitaloceanspaces.com/unittests/text_file.txt"

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act - Get the file content from the URL and upload the file
    response = requests.get(test_file_url)
    file_content = response.content
    file_name = test_file_url.split('/')[-1]

    upload_response = client.post("/common/file/upload",
                                  headers=headers,
                                  files={"file": (file_name, file_content, "image/jpg")},
                                  data={"file_type": "website"})

    # Assert - Check upload failure
    assert upload_response.status_code == 415
    assert upload_response.json() == {"detail": "Unsupported file type."}

def test_delete_uploaded_file():
    # Execute the upload test to get the necessary details
    full_file_path, jwt_token = test_upload_file()
    uploaded_file_name = full_file_path.split("/")[-1]
    # Extract file type and file extension from the uploaded file name
    file_type = "website"  # Replace with actual file type
    file_ext = uploaded_file_name.split(".")[-1]  # Assuming file_name includes the extension
    file_name = uploaded_file_name.split(".")[0]  # Assuming file_name includes the extension

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act - Delete the uploaded file
    response = client.delete(f"/common/file/delete?file_type={file_type}&file_name={file_name}&file_ext={file_ext}",
                             headers=headers)

    # Assert - Check deletion success
    assert response.status_code == 200
    assert response.json() == {"detail": "File deleted successfully."}