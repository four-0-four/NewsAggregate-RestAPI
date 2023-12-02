# app/controllers/language_controller.py
from ..services import languageService
from fastapi import HTTPException, Path, APIRouter, Depends
from starlette import status
from sqlalchemy.orm import Session
from typing import Annotated

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session, Depends(get_db)]


router = APIRouter(
    prefix="/languages", 
    tags=["Languages"]
)

@router.get("/languages", status_code=status.HTTP_200_OK)
def read_all_languages(db: Session = Depends(get_db)):
    return languageService.get_all_language(db)

@router.get("/languages/{id}", status_code=status.HTTP_200_OK)
def read_language(id: int = Path(gt=0), db: Session = Depends(get_db)):
    language = languageService.get_language(db, id)
    if language is None:
        raise HTTPException(status_code=404, detail="Language not found")
    return language
