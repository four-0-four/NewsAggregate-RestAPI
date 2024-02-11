# important to add
import json
import sys
import os
from pydantic import ValidationError
sys.path.append(os.getcwd())

import pytest
from fastapi.testclient import TestClient
from app.services.authService import decode_jwt
from main import app
from app.models.user import UserInput
import secrets

client = TestClient(app)

def test_register_existing_email():
    # Arrange
    existing_user = UserInput(
        username="sina3",
        email="msina.raf@gmail.com",
        first_name="Existing",
        last_name="User",
        password="ExistingPassword123!",
        confirmPassword="ExistingPassword123!",
        role="user"
    )

    # Act
    response = client.post("/auth/user/signup", json=existing_user.dict())

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already in use and verified"}

def test_register_invalid_password():
    try:
        invalid_password_user = UserInput(
            username="invalidpassworduser",
            email="invalidpassworduser@example.com",
            first_name="Invalid",
            last_name="Password",
            password="short",
            confirmPassword="short",
            role="user"
        )

        response = client.post("/auth/user/signup", json=invalid_password_user.dict())
    except ValidationError as e:
        error_message = str(e)
        assert "2 validation errors for UserInput" in error_message
        assert "password\n  String should have at least 8 characters" in error_message
        assert "confirmPassword\n  String should have at least 8 characters" in error_message


def login_test_user():
    # Arrange
    valid_user = {
        "username": "anonymous_19932457",
        "password": "s1i1n1a1"
    }

    # Act
    response = client.post("/auth/user/login", data=valid_user)

    # Decode the JWT
    token_data = decode_jwt(response.json()["access_token"])

    return {"token_data": token_data, "response": response, "valid_user": valid_user}

def test_login_valid_user():
    logged_in_user = login_test_user()
    token_data = logged_in_user['token_data']
    response = logged_in_user['response']
    valid_user = logged_in_user['valid_user']
    # Check the username
    assert token_data["sub"] == valid_user["username"]
    assert token_data["user"]["is_active"] == True

    # Assert
    assert response.status_code == 200
    assert "access_token" in response.json()
    
    return response.json()["access_token"]
    
def test_login_inactive_user():
    # Arrange
    valid_user = {
        "username": "sina2",
        "password": "sinasina12"
    }

    # Act
    response = client.post("/auth/user/login", data=valid_user)
    
    # Assert
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Please click on the activation link in your email to activate your account"
    }

def test_login_invalid_user():
    # Arrange
    invalid_user = {
        "username": "invaliduser",
        "password": "InvalidPassword123!"
    }

    # Act
    response = client.post("/auth/user/login", data=invalid_user)

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail":"Incorrect username/email or password"}
    
def test_login_incorrect_password():
    # Arrange
    invalid_user = {
        "username": "sina",
        "password": "InvalidPassword123!"
    }

    # Act
    response = client.post("/auth/user/login", data=invalid_user)

    # Assert
    assert response.status_code == 401
    assert response.json() == {"detail":"Incorrect username/email or password"}
    
def test_login_no_username():
    # Arrange
    invalid_user = {
        "password": "ValidPassword123!"
    }

    # Act
    response = client.post("/auth/user/login", data=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "username" in response.json()["detail"][0]["loc"]

def test_login_no_password():
    # Arrange
    invalid_user = {
        "username": "validuser"
    }

    # Act
    response = client.post("/auth/user/login", data=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]


def test_register_no_password():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]
    
def test_register_no_email():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123!",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_register_no_first_name():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "email": "test@example.com",
        "last_name": "User",
        "password": "TestPassword123!",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "first_name" in response.json()["detail"][0]["loc"]

def test_register_no_last_name():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "password": "TestPassword123!",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "last_name" in response.json()["detail"][0]["loc"]
    
def test_register_invalid_email_format():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "email": "invalidemailformat",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPassword123!",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "email" in response.json()["detail"][0]["loc"]

def test_register_password_lacks_complexity():
    # Arrange
    invalid_user = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password",
        "role": "user"
    }

    # Act
    response = client.post("/auth/user/signup", json=invalid_user)

    # Assert
    assert response.status_code == 422
    assert "password" in response.json()["detail"][0]["loc"]