from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..config.database import Base
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile

# Define the News table
class News(Base):
    """
    Table to store news articles.
    """
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)  # Title is required
    description = Column(String(800), nullable=False)  # Description can be optional
    content = Column(String(5000), nullable=False)  # Content is required
    publishedDate = Column(DateTime(timezone=True), nullable=False)  # Published date is required
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    isInternal = Column(Boolean, nullable=False, default=True)  # Default to True
    isPublished = Column(Boolean, nullable=False, default=False)  # Default to False

    # Define a relationship with NewsLocation
    locations = relationship("NewsLocation", back_populates="news")
    # Define a relationship with NewsCategory
    categories = relationship("NewsCategory", back_populates="news")
    # Define a relationship with NewsKeywords
    keywords = relationship("NewsKeywords", back_populates="news")
    # Define a relationship with NewsAffiliates
    affiliates = relationship("NewsAffiliates", back_populates="news")
    # Define a relationship with NewsMedia
    media = relationship("NewsMedia", back_populates="news")

# Define the NewsLocation table for tracking news locations
class NewsLocation(Base):
    """
    Table to store the locations associated with news articles.
    """
    __tablename__ = "newsLocations"

    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    continent_id = Column(Integer, ForeignKey('continents.id'), primary_key=True)
    country_id = Column(Integer, ForeignKey('countries.id'), primary_key=True)
    province_id = Column(Integer, ForeignKey('provinces.id'), primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.id'), primary_key=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # Define a relationship with News
    news = relationship("News", back_populates="locations")

# Define the NewsCategory table for categorizing news articles
class NewsCategory(Base):
    """
    Table to store news categories associated with articles.
    """
    __tablename__ = "newsCategories"

    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # Define a relationship with News
    news = relationship("News", back_populates="categories")

# Define the NewsKeywords table for storing keywords associated with news articles
class NewsKeywords(Base):
    """
    Table to store keywords associated with news articles.
    """
    __tablename__ = "newsKeywords"

    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), primary_key=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # Define a relationship with News
    news = relationship("News", back_populates="keywords")

# Define the NewsAffiliates table for tracking news affiliates and external links
class NewsAffiliates(Base):
    """
    Table to store news affiliates and their external links.
    """
    __tablename__ = "newsAffiliates"

    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    newsCorporation_id = Column(Integer, ForeignKey('newsCorporations.id'), primary_key=True)
    externalLink = Column(String(300), primary_key=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # Define a relationship with News
    news = relationship("News", back_populates="affiliates")

# Define the NewsMedia table for associating news articles with media sources
class NewsMedia(Base):
    """
    Table to store media sources associated with news articles.
    """
    __tablename__ = "newsMedia"

    news_id = Column(Integer, ForeignKey('news.id'), primary_key=True)
    media_id = Column(Integer, ForeignKey('media.id'), primary_key=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())

    # Define a relationship with News
    news = relationship("News", back_populates="media")


############################## pydantic models ##############################
class NewsInput(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    publishedDate: datetime
    language_id: int
    isInternal: bool = True
    isPublished: bool = False
    writer_id: int  # ID of the writer
    keywords: List[str]  # List of keyword IDs
    
    class Config:
        orm_mode = True