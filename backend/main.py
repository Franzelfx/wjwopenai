import db  # This ensures db.py is executed, which includes table creation
from fastapi import FastAPI
from routers.dashboard import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app
app = FastAPI()

# Allow origin from local angular app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the dashboard router
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
