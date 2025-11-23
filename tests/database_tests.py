from database.create_user_db import init_db
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
    """Creates a test database."""
    return init_db()

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