from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base

class Writer(Base):
    __tablename__ = "writers"  # Renamed table to follow snake_case naming convention

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)  # Renamed columns to snake_case
    last_name = Column(String(100), nullable=False)
    profile_picture_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    is_internal = Column(Boolean, nullable=False, default=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(300), nullable=False)
    linkedin_profile = Column(String(300), nullable=False)  # Renamed to snake_case
    past_experience_url = Column(String(300), nullable=False)  # Renamed to snake_case
    resume_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    email = Column(String(300), nullable=False, unique=True)

    # Define relationships
    media_profile_picture = relationship('Media', foreign_keys=[profile_picture_id])
    media_resume = relationship('Media', foreign_keys=[resume_id])
    reviews = relationship('Review', back_populates='writer')
    feedbacks = relationship('Feedback', back_populates='writer')
    news_written = relationship('News', secondary='news_writer', back_populates='writers')  # Renamed to snake_case

class WriterAffiliate(Base):
    __tablename__ = "writer_affiliates"  # Renamed to snake_case

    writer_id = Column(Integer, ForeignKey('writers.id'), primary_key=True)
    corporation_id = Column(Integer, ForeignKey('newsCorporations.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Review(Base):
    __tablename__ = "reviews"  # Renamed to snake_case

    id = Column(Integer, primary_key=True, index=True)
    writer_id = Column(Integer, ForeignKey('writers.id'), nullable=False)
    news_id = Column(Integer, ForeignKey('news.id'), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(String(800), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Define relationships
    writer = relationship('Writer', back_populates='reviews')
    media = relationship('Media', secondary='review_media', back_populates='reviews')  # Renamed to snake_case

class ReviewMedia(Base):
    __tablename__ = "review_media"  # Renamed to snake_case

    review_id = Column(Integer, ForeignKey('reviews.id'), primary_key=True)
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Feedback(Base):
    __tablename__ = "feedback"  # Renamed to snake_case

    writer_id = Column(Integer, ForeignKey('writers.id'), primary_key=True)
    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    approved = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Define relationships
    writer = relationship('Writer', back_populates='feedbacks')
    news = relationship('News', back_populates='feedbacks')

class NewsWriter(Base):
    __tablename__ = "news_writer"  # Renamed to snake_case

    writer_id = Column(Integer, ForeignKey('writers.id'), primary_key=True)
    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Define relationships
    writer = relationship('Writer', back_populates='news_written')
    news = relationship('News', back_populates='writers')
