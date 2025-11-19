from database.connection import engine
from schema.users import Base

def init_db() -> None:
    """Initializes the database tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise e

if __name__ == "__main__":
    init_db()