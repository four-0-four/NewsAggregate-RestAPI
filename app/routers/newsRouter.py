from fastapi import APIRouter, HTTPException
from .news import NewsInput, add_news
from .writer import validate_writer
from .keywords import add_keywords_to_news
from .medias import add_medias_to_news

router = APIRouter(
    prefix="/news", 
    tags=["news"]
)

'''
class NewsInput(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    publishedDate: datetime
    language_id: int
    isInternal: bool = True
    isPublished: bool = False
    writer_id: int  # ID of the writer
    keyword_ids: List[str]  # List of keyword IDs
    media_files: List[UploadFile] = []
    
    class Config:
        orm_mode = True
'''
    
@router.post("/add")
async def create_news(news_input: NewsInput):
    # Validate the writer
    if not await validate_writer(news_input.writer_id):
        raise HTTPException(status_code=400, detail="Invalid writer ID")

    # Create the news
    news = await add_news(news_input)

    # Add keywords to the news
    await add_keywords_to_news(news.id, news_input.keywords)

    # Add medias to the news
    await add_medias_to_news(news.id, news_input.medias)

    return news