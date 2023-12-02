from fastapi import FastAPI
from app.config.database import engine, Base
from app.controllers import languageController, locationController

app = FastAPI()

# Create the database tables
Base.metadata.create_all(bind=engine)


# Include routers from controllers
app.include_router(languageController.router)
app.include_router(locationController.router)