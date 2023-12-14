from sqlalchemy.orm import Session
from app.models.common import Media


async def save_media(db: Session, file_name: str, file_type: str, file_extension: str):
    new_media = Media(type=file_type, fileName=file_name, fileExtension=file_extension)
    db.add(new_media)
    db.commit()
    return new_media