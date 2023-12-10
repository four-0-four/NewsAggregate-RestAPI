# app/services/user_service.py
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from dependencies import bcrypt_context, db_dependency,oauth2_bearer
from typing import Annotated
from fastapi import Depends, HTTPException
from starlette import status
from jose import JWTError, jwt

SECRET_KEY = "e387952c4fa241f772a65daa93cd21217c3da6e2e1a4a8eb78832c464855e5ee"
ALGORITHM = "HS256"

def create_user(user_data, db: db_dependency):
    user_model = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        hashed_password=bcrypt_context.hash(user_data.password),
        is_active=True
    )
    db.add(user_model)
    db.commit()
    return user_model

async def get_current_user(token:Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {"username": username, "id": user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        
