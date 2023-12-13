# app/services/auth_service.py
import datetime
from typing import Annotated
from fastapi import HTTPException, Depends
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserInput
from app.config.dependencies import bcrypt_context, db_dependency, oauth2_bearer
from starlette import status
from os import getenv

SECRET_KEY = getenv("SECRET_KEY", "your-default-secret-key")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def create_refresh_token(data: dict):
    expires_delta = timedelta(days=7)  # Longer expiration for refresh tokens
    return create_access_token(data, expires_delta)

def validate_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

def register_user(user_data:UserInput, db: db_dependency):
    user_model = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=bcrypt_context.hash(user_data.password),
        is_active=True
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model

async def get_current_user(token:Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {"username": username, "id": user_id, 'user_role': 'user'}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
   
