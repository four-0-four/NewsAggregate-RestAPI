from app.models.writer import Writer
from sqlalchemy.orm import Session


def validate_writer(db: Session, writer_id: int) -> bool:
    writer = db.query(Writer).filter(Writer.id == writer_id).first()
    return writer is not None
