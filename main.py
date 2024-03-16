from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine, Base
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import authRouter, commonRouter, locationRouter, newsRouter, userRouter, preferenceRouter, newsSourceRouter
import uvicorn

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()


origins = [
    "http://www.farabix.com",
    "https://www.farabix.com",
    "http://farabix.com",
    "https://farabix.com",
    "https://website-buxry.ondigitalocean.app",
    "http://website-buxry.ondigitalocean.app",
    "https://website-stage-hlo64.ondigitalocean.app",
    "http://website-stage-hlo64.ondigitalocean.app",
    "https://stg.web.farabix.com",
    "http://stg.web.farabix.com",
    "http://localhost",
    "http://localhost:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(userRouter.router)
app.include_router(preferenceRouter.router)
app.include_router(newsSourceRouter.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8080, workers=4, reload=True)
    server = uvicorn.Server(config)
    server.run()