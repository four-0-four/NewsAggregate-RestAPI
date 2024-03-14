from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config.database import Base


class Tokens(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False)  # Length specified for VARCHAR
    expiration_date = Column(DateTime(timezone=True), nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    used = Column(Boolean, default=False, nullable=False)
    invalidated = Column(Boolean, default=False, nullable=False)


class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(30), nullable=False)
    fileName = Column(String(1000), nullable=False)
    fileExtension = Column(String(20), nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())


class NewsCorporations(Base):
    __tablename__ = "newsCorporations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    parent = Column(String(100))
    url = Column(String(300))
    logo = Column(String(300))
    language = Column(String(100))
    location = Column(String(100))
    
class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(50))
    native = Column(String(50))
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
class entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    parent_id = Column(Integer, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())