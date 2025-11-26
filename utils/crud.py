from schema.users import User, ChatHistory
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(db: Session, name: str, email: str, password: str) -> User:
    """Creates a new user with a hashed password."""
    hashed_password = generate_password_hash(password)
    new_user = User(
        name=name, 
        email=email, 
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieves a user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieves a user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Verifies credentials and returns the user if valid."""
    user = get_user_by_email(db, email)
    if user and check_password_hash(user.password, password):
        return user
    return None

def create_chat_entry(db: Session, user_id: int, question: str, answer: str, session_id: str) -> ChatHistory:
    """Saves a new Q&A pair to the history."""
    chat_entry = ChatHistory(
        user_id=user_id,
        session_id=session_id,
        question=question,
        answer=answer
    )
    db.add(chat_entry)
    db.commit()
    db.refresh(chat_entry)
    return chat_entry

def get_user_chat_history(db: Session, user_id: int, limit: int = 50) -> list[ChatHistory]:
    """Retrieves chat history for a specific user."""
    return db.query(ChatHistory)\
        .filter(ChatHistory.user_id == user_id)\
        .order_by(ChatHistory.created_at.desc())\
        .limit(limit)\
        .all()

def get_session_chat_history(db: Session, session_id: str, limit: int = 10) -> list[ChatHistory]:
    """Retrieves recent chat history for a specific session (for conversation memory)."""
    return db.query(ChatHistory)\
        .filter(ChatHistory.session_id == session_id)\
        .order_by(ChatHistory.created_at.desc())\
        .limit(limit)\
        .all()

def delete_chat_entry(db: Session, entry_id: int) -> bool:
    """Deletes a specific chat entry."""
    entry = db.query(ChatHistory).filter(ChatHistory.id == entry_id).first()
    if entry:
        db.delete(entry)
        db.commit()
        return True
    return False

