from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from contextlib import contextmanager

# Use an env var or default to local sqlite
DB_URL = os.getenv("DATABASE_URL", "sqlite:///bookrag.db")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Dependency for getting a DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()