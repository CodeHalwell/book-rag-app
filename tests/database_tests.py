from database.create_user_db import init_db
from utils.crud import create_user, get_user_by_email, get_user_by_id, get_user_by_email_and_password, update_chat_history, delete_chat_history, get_chat_history
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
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.id is not None
    assert user.chat_history is not None

def test_get_user_by_email(db):
    """Tests the get_user_by_email function."""
    user = get_user_by_email(db, "test@example.com")
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.id is not None
    assert user.chat_history is not None

def test_get_user_by_id(db):
    """Tests the get_user_by_id function."""
    user = get_user_by_id(db, 1)
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.id is not None
    assert user.chat_history is not None


def test_get_user_by_email_and_password(db):
    """Tests the get_user_by_email_and_password function."""
    user = get_user_by_email_and_password(db, "test@example.com", "password")
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.password is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.id is not None
    assert user.chat_history is not None

def test_update_chat_history(db):
    """Tests the update_chat_history function."""
    chat_history = update_chat_history(db, 1, "Test Question", "Test Answer")
    assert chat_history is not None
    assert chat_history.question == "Test Question"
    assert chat_history.answer == "Test Answer"
    assert chat_history.created_at is not None
    assert chat_history.updated_at is not None
    assert chat_history.id is not None
    assert chat_history.user_id is not None
    assert chat_history.user is not None

def test_delete_chat_history(db):
    """Tests the delete_chat_history function."""
    deleted = delete_chat_history(db, 1)
    assert deleted is True
    assert deleted is False

def test_get_chat_history(db):
    """Tests the get_chat_history function."""
    chat_history = get_chat_history(db, 1)
    assert chat_history is not None
    assert chat_history.question == "Test Question"
    assert chat_history.answer == "Test Answer"