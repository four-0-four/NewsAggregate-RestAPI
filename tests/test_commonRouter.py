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
    assert "file_name" in upload_response.json()

    # Get the uploaded file name for deletion
    uploaded_file_name = upload_response.json()["file_name"]

    return uploaded_file_name, jwt_token

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