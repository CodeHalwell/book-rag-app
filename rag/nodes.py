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
from utils.logging import Logging

load_dotenv()
logging = Logging()
vector_store = VectorStore(
        name=os.getenv("VECTOR_STORE_NAME", "rag_database"),
        db_path=os.getenv("VECTOR_STORE_DB_PATH", "db"),
        documents_directory=os.getenv("VECTOR_STORE_DOCUMENTS_DIRECTORY", "documents"),
    )
vector_store.initialise_vector_store()

def _get_doc_content(doc):
    """Helper to safely extract content from a document."""
    if isinstance(doc, str): return doc
    if isinstance(doc, dict): return doc.get("content", "")
    return getattr(doc, "content", str(doc))

def _get_doc_metadata(doc):
    """Helper to safely extract metadata from a document."""
    if isinstance(doc, str):
        return {"content": doc, "source_name": "unknown", "source_page": 0}
    if isinstance(doc, dict):
        return {
            "content": doc.get("content", ""),
            "source_name": doc.get("source_name", "unknown"),
            "source_page": doc.get("source_page", 0)
        }
    return {
        "content": getattr(doc, "content", str(doc)),
        "source_name": getattr(doc, "source_name", "unknown"),
        "source_page": getattr(doc, "source_page", 0)
    }

def document_retrieval_required(state: RAGState) -> RAGState:
    """Retrieves the required documents for the question."""
    retrieval_required = retrieval_required_chain(state["question"])
    return {"retrieval_required": retrieval_required}

def retrieve_documents(state: RAGState) -> RAGState:
    logging.log_info("Retrieving documents...")
    
    # Use improved question if available
    query_text = state["question"]
    retrieval_req = state.get("retrieval_required")
    if retrieval_req and hasattr(retrieval_req, "improved_question") and retrieval_req.improved_question:
        query_text = retrieval_req.improved_question
        logging.log_info(f"Using improved question for retrieval: {query_text}")
        
    raw_docs = vector_store.query_vector_store(query_text, 6)
    retrieved_docs = [
        RetrievedDocument(
            content=doc.page_content,
            source_name=doc.metadata.get("source_file", "unknown"),
            source_page=doc.metadata.get("page", 0),
            score=0.0,
            retrieved_at=datetime.now()
        ) for doc in raw_docs
    ]
    logging.log_info("Documents retrieved successfully.")
    return {"retrieved_documents": retrieved_docs, "search_queries": [query_text]}

def grade_documents(state: RAGState) -> RAGState:
    logging.log_info("Grading documents...")
    doc_strings = [_get_doc_content(doc) for doc in state["retrieved_documents"]]
    grade = grade_documents_chain(state["question"], doc_strings)
    
    # Update documents with grades
    for doc in state["retrieved_documents"]:
        if isinstance(doc, dict):
            doc["retrieval_grade"] = grade
        elif hasattr(doc, "retrieval_grade"):
            doc.retrieval_grade = grade
            
    logging.log_info("Documents graded successfully.")
    return {"retrieved_documents": state["retrieved_documents"]}

def check_retrieval_required(state: RAGState):
    """Checks if retrieval is required and handles inappropriate questions."""
    logging.log_info("Checking if retrieval is required...")
    retrieval_required_obj = state.get("retrieval_required")
    
    if retrieval_required_obj is None:
        logging.log_info("Retrieval is not required.")
        return False
    
    if retrieval_required_obj.inappropriate_question:
        logging.log_info("Question is inappropriate.")
        return "inappropriate"
    
    if retrieval_required_obj.retrieval_required:
        logging.log_info("Retrieval is required.")
        return True
    
    logging.log_info("Retrieval is not required.")
    return False
    
def generate_answer(state: RAGState) -> RAGState:
    """Generates an answer for the question."""
    logging.log_info("Generating answer...")
    doc_dicts = [_get_doc_metadata(doc) for doc in state.get("retrieved_documents", [])]
    
    logging.log_info("Documents formatted successfully.")
    answer_message = generate_answer_chain(state["question"], doc_dicts)
    
    answer_content = answer_message.content if hasattr(answer_message, 'content') else str(answer_message)
    logging.log_info("Answer generated successfully.")
    return {"answer": answer_content}

def handle_inappropriate_question(state: RAGState) -> RAGState:
    """Handles inappropriate questions by returning a polite refusal."""
    logging.log_info("Handling inappropriate question...")
    inappropriate_response = (
        "I'm sorry, but I cannot assist with that question as it appears to be "
        "inappropriate or violates content policies. Please ask a different question "
        "that I can help you with."
    )
    logging.log_info("Inappropriate question handled successfully.")
    return {"answer": inappropriate_response}
