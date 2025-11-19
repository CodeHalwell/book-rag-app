import sys
from pathlib import Path
import logging
# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.getLogger("pypdf").setLevel(logging.ERROR) 
from langchain_chroma import Chroma
from database.document_loader import DocumentLoader
from langchain_openai import OpenAIEmbeddings
import os

from dotenv import load_dotenv
load_dotenv()

class VectorStore:
    def __init__(self, name: str, db_path: str, documents_directory: str):
        self.directory = documents_directory
        self.name = name
        self.db_path = db_path
    
    def initialise_vector_store(self) -> None:
        """Initialises the vector store."""
        embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.vector_store = Chroma(
            collection_name=self.name,
            embedding_function=embeddings,
            persist_directory=self.db_path,
        )

    def upsert_documents(self) -> None:
        """
        Upserts documents into the vector store.
        The documents are preprocessed and then added to the vector store.
        """
        loader = DocumentLoader(self.directory)
        documents = loader.preprocess_documents()
        self.vector_store.add_documents(documents)


    def get_retriever(self, search_type: str = "mmr", k: int = 4, fetch_k: int = 20, lambda_mult: float = 0.5):
        """
        Returns a retriever with configurable search type (default: MMR).
        
        MMR (Maximal Marginal Relevance) optimizes for both similarity to query 
        AND diversity among selected documents.
        
        Args:
            search_type: "mmr", "similarity", or "similarity_score_threshold"
            k: Number of documents to return
            fetch_k: Amount of docs to fetch to pass to MMR algorithm (mmr only)
            lambda_mult: 0.5 = balance between relevance and diversity (mmr only)
        """
        search_kwargs = {"k": k}
        if search_type == "mmr":
            search_kwargs.update({
                "fetch_k": fetch_k, 
                "lambda_mult": lambda_mult
            })
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )

    def query_vector_store(self, query: str, k: int = 4):
        """
        Direct query using MMR by default for better results.
        """
        return self.vector_store.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=20,
            lambda_mult=0.5
        )

if __name__ == "__main__":
    vector_store = VectorStore(
        name=os.getenv("VECTOR_STORE_NAME", "rag_database"),
        db_path=os.getenv("VECTOR_STORE_DB_PATH", "db"),
        documents_directory=os.getenv("VECTOR_STORE_DOCUMENTS_DIRECTORY", "documents"),
    )
    vector_store.initialise_vector_store()
    vector_store.upsert_documents()
    print(vector_store.vector_store.get())