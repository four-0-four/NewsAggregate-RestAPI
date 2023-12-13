
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
