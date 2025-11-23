import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from database.create_user_db import init_db
from database.connection import SessionLocal, engine
from schema.users import Base, User, ChatHistory
from utils.crud import (
    create_user, 
    get_user_by_email, 
    get_user_by_id,
    authenticate_user,
    create_chat_entry,
    get_user_chat_history,
    delete_chat_entry
)
import pytest

@pytest.fixture(scope="session")
def db():   
    """Creates a test database and returns a session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    # Clean up any existing data before starting tests
    session.query(User).delete()
    session.commit()
    
    try:
        yield session
    finally:
        session.close()
        # Optional: Drop tables after tests
        # Base.metadata.drop_all(bind=engine)

def test_create_user(db):
    """Tests the create_user function."""
    user = create_user(db, "Test User", "test@example.com", "password")
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password is not None

def test_get_user_by_email(db):
    """Tests the get_user_by_email function."""
    user = get_user_by_email(db, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"

def test_authenticate_user(db):
    """Tests the authenticate_user function."""
    user = authenticate_user(db, "test@example.com", "password")
    assert user is not None
    assert user.email == "test@example.com"

def test_create_chat_entry(db):
    """Tests the create_chat_entry function."""
    user = get_user_by_id(db, 1)
    chat = create_chat_entry(db, user.id, "Test Question", "Test Answer")
    assert chat is not None
    assert chat.question == "Test Question"
    assert chat.answer == "Test Answer"

def test_get_user_chat_history(db):
    """Tests the get_user_chat_history function."""
    history = get_user_chat_history(db, 1, limit=10)
    assert len(history) > 0

def test_delete_chat_entry(db):
    """Tests the delete_chat_entry function."""
    user = get_user_by_id(db, 1)
    chat = create_chat_entry(db, user.id, "Delete Test", "Delete Answer")
    deleted = delete_chat_entry(db, chat.id)
    assert deleted is True