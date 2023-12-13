# app/controllers/auth_controller.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from requests import Session
from app.services.authService import (authenticate_user, create_access_token, 
                                      create_refresh_token, register_user, validate_refresh_token)
from app.models.user import UserInput, User
from app.config.dependencies import get_db,oauth2_bearer
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/user/signup")
@limiter.limit("8/minute")
async def create_user(request: Request, response: Response, user: UserInput, db: Session = Depends(get_db)):
    # Check if a user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    # Check if username is provided if the username is in use
    if user.username and db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already in use")

    new_user = register_user(user,db)
    
    # Create tokens after successful registration
    access_data = {"sub": new_user.username, "id": new_user.id, 'role': 'user'}
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    # Set refresh token in an HttpOnly cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/user/login")
@limiter.limit("20/minute")
async def login_for_access_token(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Try to authenticate using form_data.username as username
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # If authentication failed, try to authenticate using form_data.username as email
        user = authenticate_user(db, form_data.username, form_data.password, is_email=True)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username/email or password")
    
    access_data = {"sub": user.username, "id": user.id, 'role': 'user'}
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh/")
async def refresh_access_token(response: Response, refresh_token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    try:
        payload = validate_refresh_token(refresh_token)
        user = db.query(User).filter(User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")
        
        access_data = {"sub": user.username, "id": user.id, 'role': 'user'}
        new_access_token = create_access_token(access_data)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except HTTPException as e:
        response.delete_cookie(key="refresh_token")
        raise e
