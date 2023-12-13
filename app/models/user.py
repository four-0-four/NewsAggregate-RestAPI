from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base
from typing import Optional
from .common import Media
from pydantic import BaseModel, Field, EmailStr, validator
import re


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    profile_picture_id = Column(Integer, ForeignKey('media.id'), nullable=True)  # Allow null for profile picture
    is_active = Column(Boolean, nullable=False, default=True)  # Renamed to is_active
    username = Column(String(100), nullable=False, unique=True)
    hashed_password = Column(String(300), nullable=False)  # Renamed to hashed_password
    email = Column(String(300), nullable=False, unique=True)

    media_profile_picture = relationship('Media', foreign_keys=[profile_picture_id])


class Following(Base):
    __tablename__ = "following"

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)  # Updated foreign key reference
    writer_id = Column(Integer, ForeignKey('writers.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


################################### pydantics ###################################

class UserInput(BaseModel):
    username: Optional[str] = Field(min_length=2, max_length=100)
    email: EmailStr = Field(...)  # Validates email format
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=300)
    role: Optional[str] = Field(default='user')

    @validator('password')
    def validate_password_strength(cls, value: str):
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError('Password must contain at least one number or special character')
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "username": "user123",
                "email": "user@example.com",
                "password": "Password123!"
            }
        }
        