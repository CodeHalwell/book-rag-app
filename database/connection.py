from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
from contextlib import contextmanager

# Use an env var or default to local sqlite
DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/bookrag.db")

# Ensure data directory exists for SQLite
if DB_URL.startswith("sqlite:///") and not DB_URL.startswith("sqlite:////"):
    db_path = DB_URL.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

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