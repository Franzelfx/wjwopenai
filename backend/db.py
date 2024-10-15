import os
from dotenv import load_dotenv  # Import dotenv to load environment variables
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from a .env file
load_dotenv()

# Fetch environment variables with fallback values
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
POOL_SIZE = int(os.getenv("POOL_SIZE", 20))  # Default to 20
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", 40))  # Default to 40
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT", 30))  # Default to 30 seconds
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE", 1800))  # Default to 30 minutes

# Create the database engine with increased pool size and overflow limit
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {},
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
)

# SessionLocal class, a factory for creating new Session objects
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for creating ORM models
Base = declarative_base()

# Dependency for getting the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import the models to ensure they are registered with the Base
from models.dashboard import Project  # Import the Project model
from models.processing import ProcessingStatus  # Import the ProcessingStatus model

# Create all tables in the database
Base.metadata.create_all(bind=engine)
