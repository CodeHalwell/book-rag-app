import sys
from pathlib import Path

# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from schema.models import RAGState, RetrievedDocument
from rag.chains import retrieval_required_chain, grade_documents_chain, generate_answer_chain
from database.vector_store import VectorStore
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

vector_store = VectorStore(
        name=os.getenv("VECTOR_STORE_NAME", "rag_database"),
        db_path=os.getenv("VECTOR_STORE_DB_PATH", "db"),
        documents_directory=os.getenv("VECTOR_STORE_DOCUMENTS_DIRECTORY", "documents"),
    )

def document_retrieval_required(state: RAGState) -> RAGState:
    """Retrieves the required documents for the question.
    
    Args:
        state: The current state of the RAG graph.
    Returns:
        A RAGState object.
    """
    retrieval_required = retrieval_required_chain(state.question)
    return {"retrieval_required": retrieval_required.retrieval_required}

def retrieve_documents(state: RAGState) -> RAGState:
    raw_docs = vector_store.query_vector_store(state.question)
    retrieved_docs = []
    for doc in raw_docs:
        retrieved_docs.append(RetrievedDocument(
            content=doc.page_content,
            source_name=doc.metadata.get("source_file", "unknown"),
            source_page=doc.metadata.get("page", 0),
            score=0.0,  # MMR doesn't return scores
            retrieved_at=datetime.now()
        ))
    return {"retrieved_documents": retrieved_docs}

def grade_documents(state: RAGState) -> RAGState:
    # Extract strings from RetrievedDocument objects
    doc_strings = [doc.content for doc in state.retrieved_documents]
    grade = grade_documents_chain(state.question, doc_strings)
    # Update documents with grades
    for i, doc in enumerate(state.retrieved_documents):
        doc.retrieval_grade = grade  # Or map appropriately
    return {"retrieved_documents": state.retrieved_documents}

def check_retrieval_required(state: RAGState):
    # logic to check if retrieval_required is True/False in state
    if state.get("retrieval_required"):
        return True
    return False
    
def generate_answer(state: RAGState) -> RAGState:
    """Generates an answer for the question.
    
    Args:
        state: The current state of the RAG graph.
    Returns:
        A RAGState object.
    """
    answer = generate_answer_chain(state.question, state.retrieved_documents)
    return {"answer": answer}
