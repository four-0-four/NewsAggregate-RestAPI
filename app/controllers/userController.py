from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import Annotated
from app.services.userService import create_user, authenticate_user, create_access_token
from app.models.user import CreateUserRequest
from dependencies import db_dependency, get_db  # Import the get_db function


router = APIRouter(prefix="/user", tags=["user"])

@router.post("/signup")
async def create_user(user: CreateUserRequest, db: db_dependency = Depends(get_db)):  # Use the get_db function as a dependency
    return create_user(user, db)

@router.post("/login")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}