from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# SQLite needs a special argument to allow multiple threads (FastAPI uses threads)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True if you want to see raw SQL in the terminal
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()


def get_db():
    """Dependency to provide a database session to API routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()