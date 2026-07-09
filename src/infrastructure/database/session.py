import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# Determine if we should fall back to SQLite (e.g. running locally outside Docker container)
db_url = settings.DATABASE_URL
connect_args = {}

if settings.POSTGRES_HOST == "db" and not os.path.exists("/.dockerenv"):
    print("Notice: PostgreSQL container host 'db' is configured, but running outside Docker. Falling back to local SQLite database (ocr_local.db).")
    db_url = "sqlite:///./ocr_local.db"
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args
    )
except Exception as e:
    print(f"Warning: Failed to connect to PostgreSQL engine: {e}. Defaulting to SQLite.")
    db_url = "sqlite:///./ocr_local.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy Models
Base = declarative_base()

def get_db_context():
    """Context manager for DB session (useful for Celery workers & scripting)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
