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
import tqdm

from dotenv import load_dotenv
load_dotenv()

class VectorStore:
    def __init__(self, name: str, db_path: str, documents_directory: str):
        self.directory = documents_directory
        self.name = name
        self.db_path = db_path
    
    def initialise_vector_store(self) -> None:
        """
        Wakes up the vector store.
        If it's not there, Chroma will create it. If it is, we just load it.
        It's like opening the library doors.
        """
        embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.vector_store = Chroma(
            collection_name=self.name,
            embedding_function=embeddings,
            persist_directory=self.db_path,
        )
        print("Vector store initialised successfully.")


    def upsert_documents(self) -> None:
        """
        Stuffs the vector store with knowledge.
        We process the docs, batch them up (because Chroma gets full), and shove them in.
        """
        loader = DocumentLoader(self.directory)
        documents = loader.preprocess_documents()
        
        # ChromaDB has a max batch size limit, so we need to batch the documents
        batch_size = 5000  # Safe batch size under ChromaDB's limit of 5461
        total_docs = len(documents)
        
        print(f"Adding {total_docs} documents in batches of {batch_size}...")
        
        for i in tqdm.tqdm(range(0, total_docs, batch_size), desc="Adding documents"):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_docs + batch_size - 1) // batch_size
            
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)...")
            self.vector_store.add_documents(batch)
        
        print(f"Successfully added all {total_docs} documents to the vector store.")


    def get_retriever(self, search_type: str = "mmr", k: int = 4, fetch_k: int = 20, lambda_mult: float = 0.5):
        """
        Returns a tool to fetch documents.
        
        MMR (Maximal Marginal Relevance) is the default because it tries to find distinct info
        rather than just giving you 5 versions of the same paragraph.
        
        Args:
            search_type: How to search (MMR is usually best).
            k: How many docs you want.
            fetch_k: How many to look at before picking the best ones (for MMR).
            lambda_mult: Diversity vs Relevance slider.
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

    def query_vector_store(self, query: str, k: int = 6):
        """
        Simple direct query. 
        Uses MMR to keep things fresh and diverse.
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