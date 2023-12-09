from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class User(Base):
    __tablename__ = "users"  # Renamed table to follow snake_case naming convention

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)  # Renamed columns to snake_case
    last_name = Column(String(100), nullable=False)
    profile_picture_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    is_internal = Column(Boolean, nullable=False, default=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(300), nullable=False)
    email = Column(String(300), nullable=False, unique=True)

    # Define one-to-one relationship with Media for profile picture
    media_profile_picture = relationship('Media', foreign_keys=[profile_picture_id])

class Following(Base):
    __tablename__ = "following"

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)  # Updated foreign key reference
    writer_id = Column(Integer, ForeignKey('writers.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
