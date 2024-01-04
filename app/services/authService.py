# app/services/auth_service.py
import datetime
from typing import Annotated
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import DeleteUserInput, User, UserInput
from app.config.dependencies import bcrypt_context, db_dependency, oauth2_bearer
from starlette import status
from os import getenv
import random
import string

SECRET_KEY = getenv("SECRET_KEY", "your-default-secret-key")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

###################################endpoint functions##############################################


# delete user
def delete_user_func(
    request: Request, response: Response, db: Session, username: str
):
    # Retrieve the user from the database
    user = db.query(User).filter(User.username == username).first()

    # Check if the user exists
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user
    db.delete(user)
    db.commit()

    return {"detail": "User deleted successfully"}


def generate_random_username(length=8):
    """Generate a random username."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def register_user(request: Request, response: Response, user: UserInput, db: db_dependency):
    # Check if a user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Check if username is provided, if not, generate a random one
    if not user.username or db.query(User).filter(User.username == user.username).first():
        user.username = generate_random_username()
        # Ensure the generated username is also unique
        while db.query(User).filter(User.username == user.username).first():
            user.username = generate_random_username()

    new_user = add_user_to_db(user, db)

    # Create tokens after successful registration
    access_data = {
        "sub": new_user.username,
        "id": new_user.id,
        "role": "user",
        "user": user_to_json(new_user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    # Set refresh token in an HttpOnly cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return {"access_token": access_token, "token_type": "bearer"}


def login_user(
    request: Request,
    response: Response,
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Try to authenticate using form_data.username as username
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # If authentication failed, try to authenticate using form_data.username as email
        user = authenticate_user(
            db, form_data.username, form_data.password, is_email=True
        )
        if not user:
            raise HTTPException(
                status_code=401, detail="Incorrect username/email or password"
            )

    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Please click on the activation link in your email to activate your account",
        )

    access_data = {
        "sub": user.username,
        "id": user.id,
        "role": "user",
        "user": user_to_json(user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}


def get_refresh_token(
    response: Response, db: db_dependency, refresh_token: str = Depends(oauth2_bearer)
):
    try:
        payload = validate_refresh_token(refresh_token)
        user = db.query(User).filter(User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        access_data = {"sub": user.username, "id": user.id, "role": "user"}
        new_access_token = create_access_token(access_data)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException as e:
        response.delete_cookie(key="refresh_token")
        raise e


################################### helper functions ##############################################


def user_to_json(user: User):
    return {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
    }


def verify_password(plain_password: str, hashed_password: str):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str, is_email=False):
    if is_email:
        user = db.query(User).filter(User.email == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expires = datetime.datetime.utcnow() + expires_delta
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str):
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_refresh_token(data: dict):
    expires_delta = timedelta(days=7)  # Longer expiration for refresh tokens
    return create_access_token(data, expires_delta)


def validate_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


def add_user_to_db(user_data: UserInput, db: db_dependency):
    user_model = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=bcrypt_context.hash(user_data.password),
        is_active=False,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"username": username, "id": user_id, "user_role": "user"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
