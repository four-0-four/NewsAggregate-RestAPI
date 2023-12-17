from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine, Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import authRouter, commonRouter, locationRouter, newsRouter

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Add limiter to the application
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Include routers from controllers
app.include_router(authRouter.router)
app.include_router(locationRouter.router)
app.include_router(commonRouter.router)
app.include_router(newsRouter.router)
