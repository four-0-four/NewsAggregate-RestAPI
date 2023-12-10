# app/services/auth_service.py
import datetime
from typing import Annotated
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from dependencies import bcrypt_context, db_dependency

SECRET_KEY = "e387952c4fa241f772a65daa93cd21217c3da6e2e1a4a8eb78832c464855e5ee"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt_context.verify(password, user.password):
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = {"sub": username, "id": user_id, 'role': role}
    expires = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
