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
from langchain_core.runnables import RunnableConfig

load_dotenv()
logging = Logging()
vector_store = VectorStore(
        name=os.getenv("VECTOR_STORE_NAME", "rag_database"),
        db_path=os.getenv("VECTOR_STORE_DB_PATH", "db"),
        documents_directory=os.getenv("VECTOR_STORE_DOCUMENTS_DIRECTORY", "documents"),
    )
vector_store.initialise_vector_store()

def _get_doc_content(doc):
    """
    Extracts the juicy content from a document, safely handling different formats.
    If it's a dictionary, we grab 'content'. If it's an object, we look for a 'content' attribute.
    If it's just a string, well, that's easy.
    """
    if isinstance(doc, str):
        return doc
    if isinstance(doc, dict):
        return doc.get("content", "")
    return getattr(doc, "content", str(doc))

def _get_doc_metadata(doc):
    """
    Digs out the metadata (source, page number) so we can cite our sources properly.
    Nobody likes a claim without a citation, right?
    """
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
    """
    Decides if we actually need to go digging through the vector database.
    Sometimes the user just wants to say 'hi', and we don't need to read 50 docs for that.
    """
    logging.log_info("--- NODE: Document Retrieval Required ---")
    retrieval_required = retrieval_required_chain(state["question"])
    return {"retrieval_required": retrieval_required}

def retrieve_documents(state: RAGState) -> RAGState:
    """
    The heavy lifting. This node dives into the vector store and pulls out the most relevant chunks of text.
    It's like a librarian fetching the exact books you need.
    """
    logging.log_info("--- NODE: Retrieve Documents ---")

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
    logging.log_info(f"Documents retrieved successfully. Count: {len(retrieved_docs)}")
    return {"retrieved_documents": retrieved_docs, "search_queries": [query_text]}

def grade_documents(state: RAGState) -> RAGState:
    """
    Quality control. We take a look at what we retrieved and give it a grade.
    Are these documents actually useful, or did we just find some random noise?
    """
    logging.log_info("--- NODE: Grade Documents ---")
    logging.log_info("Grading documents...")
    doc_strings = [_get_doc_content(doc) for doc in state["retrieved_documents"]]
    grade = grade_documents_chain(state["question"], doc_strings)
    
    # Update documents with grades
    for doc in state["retrieved_documents"]:
        if isinstance(doc, dict):
            doc["retrieval_grade"] = grade
        elif hasattr(doc, "retrieval_grade"):
            doc.retrieval_grade = grade
            
    logging.log_info(f"Documents graded. Grade: {grade}")
    return {"retrieved_documents": state["retrieved_documents"]}

def check_retrieval_required(state: RAGState):
    """
    Traffic cop logic. 
    Based on what the 'retrieval_required' node said, we decide where to go next.
    - Inappropriate? -> Shut it down politely.
    - Needs docs? -> Go get 'em.
    - Just chatting? -> Skip straight to the answer.
    """
    logging.log_info("--- EDGE: Check Retrieval Required ---")
    logging.log_info("Checking if retrieval is required...")
    retrieval_required_obj = state.get("retrieval_required")
    
    if retrieval_required_obj is None:
        logging.log_info("DECISION: Retrieval NOT required (Default)")
        return False
    
    if retrieval_required_obj.inappropriate_question:
        logging.log_info("DECISION: Question is Inappropriate -> Handle Inappropriate")
        return "inappropriate"
    
    if retrieval_required_obj.retrieval_required:
        logging.log_info("DECISION: Retrieval Required -> Retrieve Documents")
        return True
    
    logging.log_info("DECISION: Retrieval NOT required -> Generate Answer")
    return False

    
def generate_answer(state: RAGState, config: RunnableConfig) -> RAGState:
    """
    The grand finale. We take the question and (optionally) the docs, and craft a beautiful answer.
    If we're streaming, we hook up the callbacks here so the user sees text flying onto the screen.
    """
    logging.log_info("--- NODE: Generate Answer ---")
    logging.log_info("Generating answer...")
    doc_dicts = [_get_doc_metadata(doc) for doc in state.get("retrieved_documents", [])]
    
    logging.log_info(f"Formatting {len(doc_dicts)} documents for the prompt.")
    
    callbacks = []
    if config and "configurable" in config:
        stream_callback = config["configurable"].get("stream_callback")
        if stream_callback:
            callbacks = [stream_callback]
            
    answer_message = generate_answer_chain(state["question"], doc_dicts, callbacks=callbacks)
    
    answer_content = answer_message.content if hasattr(answer_message, 'content') else str(answer_message)
    logging.log_info("Answer generated successfully.")
    return {"answer": answer_content}

def handle_inappropriate_question(state: RAGState) -> RAGState:
    """
    The bouncer node. If someone asks something naughty, we politely show them the door.
    """
    logging.log_info("--- NODE: Handle Inappropriate Question ---")
    logging.log_info("Handling inappropriate question...")
    inappropriate_response = (
        "I'm sorry, but I cannot assist with that question as it appears to be "
        "inappropriate or violates content policies. Please ask a different question "
        "that I can help you with."
    )
    logging.log_info("Inappropriate question handled successfully.")
    return {"answer": inappropriate_response}
