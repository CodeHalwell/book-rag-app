import sys
from pathlib import Path

# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from database.vector_store import VectorStore
import os
from dotenv import load_dotenv
load_dotenv()

def process_documents() -> None:
    """Processes the documents and upserts them into the vector store."""
    try:
        vector_store = VectorStore(
            name=os.getenv("VECTOR_STORE_NAME", "rag_database"),
            db_path=os.getenv("VECTOR_STORE_DB_PATH", "db"),
            documents_directory=os.getenv("VECTOR_STORE_DOCUMENTS_DIRECTORY", "documents"),
        )

        vector_store.initialise_vector_store()
        vector_store.upsert_documents()
    except Exception as e:
        print(f"Error processing documents: {e}")
        raise e
    finally:
        print("Documents processed successfully!")
        
if __name__ == "__main__":
    process_documents()