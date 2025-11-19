import sys
from pathlib import Path

# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from langgraph.graph import StateGraph, START, END
from schema.models import RAGState
from rag.nodes import document_retrieval_required, retrieve_documents, grade_documents, generate_answer, check_retrieval_required

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

state_schema = RAGState
graph = StateGraph(state_schema)

  
def build_graph():
    graph = StateGraph(state_schema)
    
    graph.add_node("document_retrieval_required", document_retrieval_required)
    graph.add_node("retrieve_documents", retrieve_documents)
    graph.add_node("grade_documents", grade_documents)
    graph.add_node("generate_answer", generate_answer)

    graph.add_edge(START, "document_retrieval_required")
    graph.add_conditional_edges(
        "document_retrieval_required",
        check_retrieval_required,
        {
            True: "retrieve_documents",
            False: "generate_answer",
        }
    )
    graph.add_edge("retrieve_documents", "grade_documents")
    graph.add_edge("grade_documents", "generate_answer")
    graph.add_edge("generate_answer", END)

    compiled_graph = graph.compile()

    return compiled_graph
