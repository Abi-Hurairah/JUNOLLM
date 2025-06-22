import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set.")

# The engine is the main entry point to the database.
# echo=True is useful for debugging to see the generated SQL.
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """
    Initializes the database by creating all tables defined by SQLModel.
    This should be called once when the application starts.
    """
    # This assumes your SQLModel classes are imported somewhere before this runs
    # (e.g., in models.py, which is imported by main.py)
    import models 
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    FastAPI dependency that provides a database session for a single request.
    It ensures the session is always closed after the request is finished.
    """
    with Session(engine) as session:
        yield session

