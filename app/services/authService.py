# app/services/auth_service.py
from typing import Annotated
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.common import Tokens
from app.models.user import DeleteUserInput, User, UserInput
from app.config.dependencies import bcrypt_context, db_dependency, oauth2_bearer
from starlette import status
from os import getenv
import random
import string
from fastapi import HTTPException, Request, Response
from itsdangerous import URLSafeTimedSerializer

from app.email.sendEmail import sendEmail

SECRET_KEY = getenv("SECRET_KEY", "your-default-secret-key")
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

###################################endpoint functions##############################################

FORGET_SECRET_KEY = "your_secret_key"  # Use a strong, unique key
FORGET_SECURITY_PASSWORD_SALT = "your_security_salt"


# delete user
def delete_user_func(
    request: Request, response: Response, db: Session, username: str
):
    # Retrieve the user from the database
    user = db.query(User).filter(User.username == username).first()

    # Check if the user exists
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user
    db.delete(user)
    db.commit()

    return {"detail": "User deleted successfully"}


def generate_random_username(length=8):
    """Generate a random username."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def register_user(request: Request, response: Response, user: UserInput, db: db_dependency):
    # Password Confirmation Check
    if user.password != user.confirmPassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Check if a user with the same email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        if not existing_user.is_active:  # Check if the existing user is not active
            # Generate a new activation token (implement this function)
            token = generate_token(existing_user.email, db)

            # Send an email with the activation link (implement send_activation_email)
            activation_link = f"http://localhost:3000/auth/ActivateAccount?token={token}"
            sendEmail("Farabix Support <admin@farabix.com>", user.email, "Activate Your Account", activation_link)

            raise HTTPException(status_code=400, detail="User already exists but is not verified. An activation email has been sent. Please check your email.")
        else:
            raise HTTPException(status_code=400, detail="Email already in use and verified")

    # Check if username is provided, if not, generate a random one
    if not user.username:
        user.username = generate_random_username()
        # Ensure the generated username is also unique
        while db.query(User).filter(User.username == user.username).first():
            user.username = generate_random_username()
    elif db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already in use")

    new_user = add_user_to_db(user, db)

    # Generate a password reset token (you need to implement this)
    token = generate_token(new_user.email, db)

    # Send an email with the password reset link (implement send_reset_email)
    reset_link = f"http://localhost:3000/auth/ActivateAccount?token={token}"
    sendEmail("Farabix Support <admin@farabix.com>", user.email, "activateAccount", reset_link)

    return {"message": "An Email sent to your email address, please check your email to activate your account"}

def get_loggedin_user(request: Request, db: db_dependency):
    # Extract the token from the request headers
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No access token provided")

    # Remove the 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Retrieve the user from the database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user_to_json(user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def login_user(
    request: Request,
    response: Response,
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Try to authenticate using form_data.username as username
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # If authentication failed, try to authenticate using form_data.username as email
        user = authenticate_user(
            db, form_data.username, form_data.password, is_email=True
        )
        if not user:
            raise HTTPException(
                status_code=401, detail="Incorrect username/email or password"
            )

    # Check if the user is active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Please click on the activation link in your email to activate your account",
        )

    access_data = {
        "sub": user.username,
        "id": user.id,
        "role": "user",
        "user": user_to_json(user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}




def generate_token(email, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with given email not found")

    # Invalidate existing tokens that are not yet expired
    current_time = datetime.utcnow()
    tokens = db.query(Tokens).filter(
        Tokens.user_id == user.id,
        Tokens.expiration_date > current_time,
        Tokens.used == False
    ).all()

    for token in tokens:
        token.invalidated = True

    # Serialize data for new token
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    token_string = serializer.dumps(email, salt=FORGET_SECURITY_PASSWORD_SALT)

    # Create new token object
    expiration_date = current_time + timedelta(seconds=900)  # 15 minutes from now
    new_token = Tokens(
        user_id=user.id,
        token=token_string,
        expiration_date=expiration_date,
        used=False,
        invalidated=False
    )

    # Add new token to database
    db.add(new_token)
    db.commit()

    return token_string


def check_token(token_str, db, activateIt=False, expiration=3600):
    # Find the token in the database
    token = db.query(Tokens).filter(Tokens.token == token_str).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Check if the token is expired
    if datetime.utcnow() > token.expiration_date:
        raise HTTPException(status_code=400, detail="Token expired")

    # Check if the token has already been used
    if token.used or token.invalidated:
        raise HTTPException(status_code=400, detail="Token has been used or invalidated")

    # Deserialize token to get the email
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(
            token_str,
            salt=FORGET_SECURITY_PASSWORD_SALT,
            max_age=expiration
        )
    except:
        raise HTTPException(status_code=400, detail="Invalid token")

    # Check if the email matches the token's user
    user = db.query(User).filter(User.id == token.user_id).first()
    if not user or user.email != email:
        raise HTTPException(status_code=400, detail="Email does not match token")

    # Mark the token as used
    if activateIt:
        token.used = True
    db.commit()

    return user


def confirm_token_and_activate_account(token_str, db):
    user = check_token(token_str, db, True)
    user.is_active = True
    db.commit()
    return {"message": "Account activated successfully"}


def confirm_token_and_getEmail(token_str, db, expiration=3600):
    user = check_token(token_str, db, True, expiration=expiration)
    return user.email


def initiate_password_reset(email: str, db: db_dependency):
    # Check if a user with the given email exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with given email not found")

    # Generate a password reset token (you need to implement this)
    reset_token = generate_token(email, db)

    # Send an email with the password reset link (implement send_reset_email)
    reset_link = f"http://localhost:3000/auth/ChangePassword?token={reset_token}"
    sendEmail("Farabix Support <admin@farabix.com>", user.email, "forgetPassword", reset_link)

    return {"message": "If an account with that email exists, a password reset link has been sent."}



def get_refresh_token(
    response: Response, db: db_dependency, refresh_token: str = Depends(oauth2_bearer)
):
    try:
        payload = validate_refresh_token(refresh_token)
        user = db.query(User).filter(User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        # Create new access and refresh tokens
        access_data = {"sub": user.username, "id": user.id, "role": "user"}
        new_access_token = create_access_token(access_data)
        new_refresh_token = create_refresh_token(access_data)

        # Set new refresh token in an HttpOnly cookie
        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True)

        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        response.delete_cookie(key="refresh_token")
        raise e


def change_password(token_str: str, new_password: str, confirm_password: str, db):
    # Confirm the token
    email = confirm_token_and_getEmail(token_str, db)

    # Check if new_password and confirm_password match
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Retrieve user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user's password using bcrypt hashing
    user.hashed_password = bcrypt_context.hash(new_password)
    db.commit()

    # Create access and refresh tokens for the user
    access_data = {
        "sub": user.username,
        "id": user.id,
        "role": "user",
        "user": user_to_json(user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    # Return the access token (logging the user in)
    return {"access_token": access_token, "token_type": "bearer"}


################################### helper functions ##############################################


def user_to_json(user: User):
    return {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
    }


def verify_password(plain_password: str, hashed_password: str):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str, is_email=False):
    if is_email:
        user = db.query(User).filter(User.email == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    expires = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_jwt(token: str):
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Signature has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_refresh_token(data: dict):
    expires_delta = timedelta(days=7)  # Longer expiration for refresh tokens
    return create_access_token(data, expires_delta)


def validate_refresh_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


def add_user_to_db(user_data: UserInput, db: db_dependency):
    user_model = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=bcrypt_context.hash(user_data.password),
        is_active=False,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return user_model


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"username": username, "id": user_id, "user_role": "user"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
