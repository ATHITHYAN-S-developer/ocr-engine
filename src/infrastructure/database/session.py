from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

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
