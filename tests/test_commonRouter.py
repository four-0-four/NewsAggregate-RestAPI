# important to add
import json
import sys
import os
from pydantic import ValidationError
sys.path.append(os.getcwd())
from fastapi.testclient import TestClient
from main import app
from tests.test_authRouter import test_login_valid_user

client = TestClient(app)

def test_upload_file():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Arrange for file upload
    test_file_path = "./tests/test_file.jpg"

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act - Upload the file
    with open(test_file_path, "rb") as file:
        response = client.post("/common/file/upload", 
                               headers=headers,
                               files={"file": (test_file_path, file, "image/jpg")},
                               data={"file_type": "website"})

    # Assert - Check upload success
    assert response.status_code == 200
    assert "file_name" in response.json()

    # Get the uploaded file name for deletion
    uploaded_file_name = response.json()["file_name"]

    return uploaded_file_name, jwt_token

def test_upload_invalid_file_type():
    # Login and get JWT token
    jwt_token = test_login_valid_user()

    # Arrange for file uploads
    test_file_path = "./tests/text_file.txt"

    # Headers with Authorization
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Act - Upload the file
    with open(test_file_path, "rb") as file:
        response = client.post("/common/file/upload", 
                               headers=headers,
                               files={"file": (test_file_path, file, "image/jpg")},
                               data={"file_type": "website"})

    # Assert - Check upload success
    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported file type."}

def test_delete_uploaded_file():
    # Execute the upload test to get the necessary details
    uploaded_file_name, jwt_token = test_upload_file()

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