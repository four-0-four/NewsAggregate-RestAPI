# app/controllers/language_controller.py
from ..services import locationService
from fastapi import HTTPException, Path, APIRouter, Depends
from starlette import status
from sqlalchemy.orm import Session
from typing import Annotated
from ..config.database import SessionLocal
from app.config.dependencies import get_db


router = APIRouter(prefix="/locations", tags=["Locations"])


@router.get("/continents/{id}", status_code=status.HTTP_200_OK)
def read_continent(id: int = Path(gt=0), db: Session = Depends(get_db)):
    continent = locationService.get_continent(db, id)
    if continent is None:
        raise HTTPException(status_code=404, detail="Continent not found")
    return continent


@router.get("/countries/{id}", status_code=status.HTTP_200_OK)
def read_country(id: int = Path(gt=0), db: Session = Depends(get_db)):
    country = locationService.get_country(db, id)
    if country is None:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.get("/provinces/{id}", status_code=status.HTTP_200_OK)
def read_province(id: int = Path(gt=0), db: Session = Depends(get_db)):
    province = locationService.get_province(db, id)
    if province is None:
        raise HTTPException(status_code=404, detail="Province not found")
    return province


@router.get("/cities/{id}", status_code=status.HTTP_200_OK)
def read_city(id: int = Path(gt=0), db: Session = Depends(get_db)):
    city = locationService.get_city(db, id)
    if city is None:
        raise HTTPException(status_code=404, detail="City not found")
    return city
