import db  # This ensures db.py is executed, which includes table creation
from fastapi import FastAPI
from dotenv import load_dotenv
from routers.processing import router as processing_router
from routers.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Allow origin from local angular app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()  # Load environment variables from .env file

# Include the dashboard router
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(processing_router, prefix="/processing", tags=["processing"])