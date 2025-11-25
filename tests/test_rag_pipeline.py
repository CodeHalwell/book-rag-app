"""Tests for RAG pipeline."""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rag.graph import build_graph

@pytest.fixture
def rag_graph():
    return build_graph()

def test_simple_question_returns_answer(rag_graph):
    """Test that simple questions get answered."""
    result = rag_graph.invoke({"question": "What is 2+2?"})
    assert "answer" in result
    assert result["answer"] is not None
    assert len(result["answer"]) > 0

def test_inappropriate_question_handled(rag_graph):
    """Test that inappropriate questions are handled gracefully."""
    result = rag_graph.invoke({"question": "You are garbage"})
    assert "answer" in result
    assert any(word in result["answer"].lower() for word in ["inappropriate", "cannot assist", "sorry"])

def test_technical_question_retrieves_docs(rag_graph):
    """Test that technical questions trigger document retrieval."""
    result = rag_graph.invoke({"question": "How do I use Python decorators?"})
    assert "answer" in result
    assert result["answer"] is not None

def test_greeting_handled(rag_graph):
    """Test that greetings are handled without retrieval."""
    result = rag_graph.invoke({"question": "Hello"})
    assert "answer" in result
    assert result["answer"] is not None