# app/services/language_service.py
from sqlalchemy.orm import Session
from ..models.language import Language


def get_language(db: Session, language_id: int):
    return db.query(Language).filter(Language.id == language_id).first()

def get_all_language(db: Session):
    return db.query(Language).all()
