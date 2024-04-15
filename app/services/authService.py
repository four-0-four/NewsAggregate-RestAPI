# app/services/auth_service.py
from typing import Annotated
from fastapi import HTTPException, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.data.newsSourceData import insert_default_news_sources_for_user

from app.models.common import Tokens
from app.models.user import DeleteUserInput, User, UserInput
from app.config.dependencies import bcrypt_context, db_dependency, oauth2_bearer
from starlette import status
from os import getenv
import random
import string
from fastapi import HTTPException, Request, Response
from itsdangerous import URLSafeTimedSerializer
import aiomysql

from app.config.database import conn_params
from app.email.sendEmail import sendEmail

SECRET_KEY = getenv("SECRET_KEY", "your-default-secret-key")
BASE_URL = getenv("BASE_URL", "http://localhost:3000")
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


def generate_random_username():
    """Generate a random username for a journalist with enhanced randomness."""
    entity = "anonymous"
    random_number = random.randint(1, 99999999)  # Expanded range for greater randomness
    return f"{entity}_{random_number}"


async def register_user(request: Request, response: Response, user: UserInput):
    # Password Confirmation Check
    if user.password != user.confirmPassword:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Check if a user with the same email already exists
                await cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1;", (user.email,))
                existing_user = await cur.fetchone()

                if existing_user:
                    if not existing_user['is_active']:
                        try:
                            token = await generate_token(existing_user['email'])
                            activation_link = f"{BASE_URL}/auth/ActivateAccount?token={token}"
                            sendEmail("Farabix Support <admin@farabix.com>", user.email, "activateAccount", activation_link)
                        except Exception as e:
                            raise HTTPException(status_code=500, detail="Failed to send activation email.")
                        raise HTTPException(status_code=400, detail="Please verify your email to complete any pending actions. We have sent you an email!")
                    else:
                        raise HTTPException(status_code=400, detail="Email already in use by another account")

                if not user.username:
                    user.username = generate_random_username()

                await cur.execute("SELECT * FROM users WHERE username = %s LIMIT 1;", (user.username,))
                while await cur.fetchone():
                    user.username = generate_random_username()

                try:
                    hashed_password = bcrypt_context.hash(user.password)
                    await cur.execute(
                        "INSERT INTO users (email, username, first_name, last_name, hashed_password, is_active) VALUES (%s, %s, %s, %s, %s, %s);",
                        (user.email, user.username, user.first_name, user.last_name, hashed_password, False)
                    )
                except Exception as e:
                    await conn.rollback()
                    raise HTTPException(status_code=500, detail="Failed to create user.")

                await conn.commit()

                # Attempt to fetch the newly created user to get the ID
                await cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1;", (user.email,))
                new_user = await cur.fetchone()
                if not new_user:
                    raise HTTPException(status_code=500, detail="Failed to fetch new user after creation.")

                # Add default news sources for user
                # Ensure this operation is critical and should not fail silently
                try:
                    await insert_default_news_sources_for_user(new_user['id'])
                except Exception as e:
                    raise HTTPException(status_code=500, detail="Failed to set up default news sources for the user.")

                # Send activation email
                try:
                    token = await generate_token(new_user['email'])
                    reset_link = f"{BASE_URL}/auth/ActivateAccount?token={token}"
                    sendEmail("Farabix Support <admin@farabix.com>", user.email, "activateAccount", reset_link)
                except Exception as e:
                    raise HTTPException(status_code=500, detail="Failed to send the activation email.")

    return {"message": "An email has been sent to your address. Please check your email to activate your account."}


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


async def login_user(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Try to authenticate using form_data.username as username
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        # If authentication failed, try to authenticate using form_data.username as email
        user = await authenticate_user(
            form_data.username, form_data.password, is_email=True
        )
        if not user:
            raise HTTPException(
                status_code=401, detail="Incorrect username/email or password"
            )

    # Check if the user is active
    if not user.get("is_active",False):
        raise HTTPException(
            status_code=403,
            detail="Please click on the activation link in your email to activate your account",
        )

    access_data = {
        "sub": user.get("username", ""),
        "id": user.get("id","" ),
        "role": "user",
        "user": new_user_to_json(user),
    }
    access_token = create_access_token(access_data)
    refresh_token = create_refresh_token(access_data)

    return {"access_token": access_token, "token_type": "bearer" , "refresh_token": refresh_token}




async def generate_token(email):
    try:
        async with aiomysql.create_pool(**conn_params) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    # Start a transaction
                    await conn.begin()

                    # Check for the user and invalidate old tokens in one go
                    await cur.execute("""
                        SELECT id FROM users WHERE email = %s LIMIT 1 FOR UPDATE;
                    """, (email,))
                    user = await cur.fetchone()

                    if not user:
                        await conn.rollback()
                        raise HTTPException(status_code=404, detail="User with given email not found")

                    current_time = datetime.utcnow()
                    # Directly invalidate all expired tokens
                    await cur.execute("""
                        UPDATE tokens SET invalidated = 1 
                        WHERE user_id = %s AND expiration_date > %s AND used = 0;
                    """, (user['id'], current_time))

                    # Serialize data for new token
                    serializer = URLSafeTimedSerializer(SECRET_KEY)
                    token_string = serializer.dumps(email, salt=FORGET_SECURITY_PASSWORD_SALT)

                    # Create new token object
                    expiration_date = current_time + timedelta(seconds=900)  # 15 minutes from now
                    await cur.execute("""
                        INSERT INTO tokens (user_id, token, expiration_date, used, invalidated) VALUES (%s, %s, %s, 0, 0);
                    """, (user['id'], token_string, expiration_date))

                    # Commit the transaction
                    await conn.commit()

                    return token_string
    except Exception as e:
        # Rollback in case of exception
        await conn.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred: " + str(e))


def check_token(token_str, db, activateIt=False, expiration=3600):
    # Find the token in the database
    token = db.query(Tokens).filter(Tokens.token == token_str).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    # Check if the token is expired
    if datetime.utcnow() > token.expiration_date:
        raise HTTPException(status_code=400, detail="Token expired")

    # Check if the token has already been used
    if token.invalidated:
        raise HTTPException(status_code=400, detail="Token has been invalidated")

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


def invalidate_token(token_str, db, expiration=3600):
    token = db.query(Tokens).filter(Tokens.token == token_str).first()
    token.invalidated = True
    db.commit()


async def initiate_password_reset(email: str, db: db_dependency):
    # Check if a user with the given email exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with given email not found")

    if not user.is_active:  # Check if the existing user is not active
        # Generate a new activation token (implement this function)
        token = await generate_token(user.email)

        # Send an email with the activation link (implement send_activation_email)
        activation_link = f"{BASE_URL}/auth/ActivateAccount?token={token}"
        sendEmail("Farabix Support <admin@farabix.com>", user.email, "activateAccount", activation_link)

        return {"message": "user is not verified yet! we sent an activation email"}


    # Generate a password reset token (you need to implement this)
    reset_token = await generate_token(email)

    # Send an email with the password reset link (implement send_reset_email)
    reset_link = f"{BASE_URL}/auth/ChangePassword?token={reset_token}"
    sendEmail("Farabix Support <admin@farabix.com>", user.email, "forgetPassword", reset_link)

    return {"message": "If an account with that email exists, a password reset link has been sent."}



def get_refresh_token(db: db_dependency, refresh_token: str):
    try:
        payload = validate_refresh_token(refresh_token)
        user = db.query(User).filter(User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        # Create new access and refresh tokens
        access_data = {"sub": user.username, "id": user.id, "role": "user"}
        new_access_token = create_access_token(access_data)
        new_refresh_token = create_refresh_token(access_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e


def change_password( response: Response, token_str: str, new_password: str, confirm_password: str, db):
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

    #invalidate token
    invalidate_token(token_str, db)

    # Return the access token (logging the user in)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


################################### helper functions ##############################################


def new_user_to_json(user: User):
    return {
        "username": user["username"],
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "is_active": user["is_active"],
    }

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


def authenticate_user2(db: Session, username: str, password: str, is_email=False):
    if is_email:
        user = db.query(User).filter(User.email == username).first()
    else:
        user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


async def authenticate_user(username: str, password: str, is_email=False):
    async with aiomysql.create_pool(**conn_params) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # Choose the correct column based on whether the username is an email
                column = "email" if is_email else "username"
                sql_query = f"SELECT * FROM users WHERE {column} = %s LIMIT 1;"

                # Execute the SQL query
                await cur.execute(sql_query, (username,))
                user = await cur.fetchone()

                if not user or not verify_password(password, user['hashed_password']):
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
