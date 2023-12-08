from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.sql import func
from ..config.database import Base

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    mediaUrl = Column(String(300))
    isVideo = Column(Boolean, default=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())


class NewsCorporations(Base):
    __tablename__ = "newsCorporations"

    id = Column(Integer, primary_key=True, index=True)
    parentOrganization = Column(String(100))
    organizationName = Column(String(100))
    yearFounded = Column(Integer)
    language_id = Column(Integer, ForeignKey('languages.id'))
    
class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, index=True)
    name = Column(String(50))
    native = Column(String(50))
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())
    
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    parent_id = Column(Integer, ForeignKey('categories.id'))
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), onupdate=func.now())