# app/controllers/auth_controller.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from requests import Session
from app.services.authService import (
    delete_user_func,
    get_refresh_token,
    register_user,
    delete_user_func,
    login_user, get_current_user, get_loggedin_user, initiate_password_reset, change_password,
    check_token,
)
from app.models.user import UserInput, User, DeleteUserInput, ChangePasswordInput
from app.config.dependencies import get_db, oauth2_bearer
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/user/signup")
async def create_user(
    request: Request,
    response: Response,
    user: UserInput,
    db: Session = Depends(get_db)
):
    return register_user(request, response, user, db)


@router.delete("/user/delete/{username}")
async def delete_user(
    request: Request, response: Response, username: str, db: Session = Depends(get_db)
):
    return delete_user_func(request, response, db, username)


@router.get("/user")
async def get_user(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    return get_loggedin_user(request, db)

@router.post("/user/login")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return login_user(request, response, db, form_data)


@router.post("/user/forget-password")
async def forget_password(request: Request, response: Response, db: Session = Depends(get_db)):
    email = await request.json()
    return initiate_password_reset(email['email'], db)


@router.post("/user/confirm-reset")
async def forget_password(request: Request, response: Response, db: Session = Depends(get_db)):
    token = await request.json()
    return check_token(token['token'], db)


@router.post("/user/change-password")
async def forget_password(request: Request, response: Response, newInfo: ChangePasswordInput, db: Session = Depends(get_db)):
    return change_password(
        newInfo.token,
        newInfo.newPassword,
        newInfo.confirmPassword,
        db
    )


@router.post("/refresh/")
async def refresh_access_token(
    response: Response,
    refresh_token: str = Depends(oauth2_bearer),
    db: Session = Depends(get_db),
):
    return get_refresh_token(response, refresh_token, db)
