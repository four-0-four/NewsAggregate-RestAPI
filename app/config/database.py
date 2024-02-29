from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
print("********************************************")
print(os.getenv("DATABASE_URL", "sqlite:///./fallback.db"))
print("********************************************")
conn_params = {
    "host": os.getenv("DATABASE_HOST", "localhost"),
    "port": int(os.getenv("DATABASE_PORT", "3306")),  # Convert port to integer
    "user": os.getenv("DATABASE_USERNAME", "root"),
    "password": os.getenv("DATABASE_PASSWORD", "password"),
    "db": os.getenv("DATABASE_NAME", "newsdb"),
}

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fallback.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()