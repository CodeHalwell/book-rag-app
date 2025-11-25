"""Tests for grade_documents node filtering and sorting."""
import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from schema.models import RAGState, RetrievedDocument, RetrievalGrade, Review


def create_mock_grade(relevant: bool, overall_score: float) -> RetrievalGrade:
    """Helper to create a mock RetrievalGrade with specified values."""
    return RetrievalGrade(
        review=Review(
            relevance=overall_score,
            usefulness=overall_score,
            accuracy=overall_score,
            completeness=overall_score,
            clarity=overall_score,
            overall_score=overall_score,
        ),
        relevant=relevant,
    )


def create_test_document(content: str) -> RetrievedDocument:
    """Helper to create a test document."""
    return RetrievedDocument(
        content=content,
        source_name="test_source.pdf",
        source_page=1,
        score=0.0,
        retrieved_at=datetime.now(),
    )


@pytest.fixture
def sample_documents():
    """Create a set of sample documents for testing."""
    return [
        create_test_document("Document about Python decorators"),
        create_test_document("Document about JavaScript frameworks"),
        create_test_document("Document about database optimization"),
        create_test_document("Unrelated document about cooking recipes"),
    ]


class TestGradeDocumentsFiltering:
    """Tests for document filtering based on relevance."""

    @patch("rag.nodes.grade_documents_chain")
    def test_filters_out_irrelevant_documents(self, mock_chain, sample_documents):
        """Test that documents marked as irrelevant are filtered out."""
        from rag.nodes import grade_documents

        # Mock grades: first two relevant, last two irrelevant
        mock_chain.side_effect = [
            create_mock_grade(relevant=True, overall_score=0.8),
            create_mock_grade(relevant=True, overall_score=0.7),
            create_mock_grade(relevant=False, overall_score=0.3),
            create_mock_grade(relevant=False, overall_score=0.2),
        ]

        state: RAGState = {
            "question": "How do I use Python decorators?",
            "retrieved_documents": sample_documents,
        }

        result = grade_documents(state)

        assert len(result["retrieved_documents"]) == 2
        assert all(doc.retrieval_grade.relevant for doc in result["retrieved_documents"])

    @patch("rag.nodes.grade_documents_chain")
    def test_keeps_all_relevant_documents(self, mock_chain, sample_documents):
        """Test that all relevant documents are kept."""
        from rag.nodes import grade_documents

        # All documents are relevant
        mock_chain.side_effect = [
            create_mock_grade(relevant=True, overall_score=0.9),
            create_mock_grade(relevant=True, overall_score=0.8),
            create_mock_grade(relevant=True, overall_score=0.7),
            create_mock_grade(relevant=True, overall_score=0.6),
        ]

        state: RAGState = {
            "question": "General programming question",
            "retrieved_documents": sample_documents,
        }

        result = grade_documents(state)

        assert len(result["retrieved_documents"]) == 4

    @patch("rag.nodes.grade_documents_chain")
    def test_returns_empty_when_all_irrelevant(self, mock_chain, sample_documents):
        """Test that empty list is returned when all documents are irrelevant."""
        from rag.nodes import grade_documents

        # All documents are irrelevant
        mock_chain.side_effect = [
            create_mock_grade(relevant=False, overall_score=0.2),
            create_mock_grade(relevant=False, overall_score=0.1),
            create_mock_grade(relevant=False, overall_score=0.15),
            create_mock_grade(relevant=False, overall_score=0.05),
        ]

        state: RAGState = {
            "question": "Completely unrelated question",
            "retrieved_documents": sample_documents,
        }

        result = grade_documents(state)

        assert len(result["retrieved_documents"]) == 0


class TestGradeDocumentsSorting:
    """Tests for document sorting based on overall_score."""

    @patch("rag.nodes.grade_documents_chain")
    def test_sorts_by_overall_score_descending(self, mock_chain, sample_documents):
        """Test that documents are sorted by overall_score in descending order."""
        from rag.nodes import grade_documents

        # Grades with varying scores (not in order)
        mock_chain.side_effect = [
            create_mock_grade(relevant=True, overall_score=0.5),  # Should be 3rd
            create_mock_grade(relevant=True, overall_score=0.9),  # Should be 1st
            create_mock_grade(relevant=True, overall_score=0.3),  # Should be 4th
            create_mock_grade(relevant=True, overall_score=0.7),  # Should be 2nd
        ]

        state: RAGState = {
            "question": "Test question",
            "retrieved_documents": sample_documents,
        }

        result = grade_documents(state)

        scores = [doc.retrieval_grade.review.overall_score for doc in result["retrieved_documents"]]
        assert scores == [0.9, 0.7, 0.5, 0.3], f"Expected descending order, got {scores}"

    @patch("rag.nodes.grade_documents_chain")
    def test_sorts_after_filtering(self, mock_chain, sample_documents):
        """Test that sorting happens after filtering irrelevant documents."""
        from rag.nodes import grade_documents

        # Mix of relevant (varying scores) and irrelevant documents
        mock_chain.side_effect = [
            create_mock_grade(relevant=True, overall_score=0.6),   # Relevant, should be 2nd
            create_mock_grade(relevant=False, overall_score=0.95), # Irrelevant, filtered out
            create_mock_grade(relevant=True, overall_score=0.8),   # Relevant, should be 1st
            create_mock_grade(relevant=False, overall_score=0.1),  # Irrelevant, filtered out
        ]

        state: RAGState = {
            "question": "Test question",
            "retrieved_documents": sample_documents,
        }

        result = grade_documents(state)

        assert len(result["retrieved_documents"]) == 2
        scores = [doc.retrieval_grade.review.overall_score for doc in result["retrieved_documents"]]
        assert scores == [0.8, 0.6], f"Expected [0.8, 0.6], got {scores}"


class TestGradeDocumentsIntegration:
    """Integration tests for grade_documents with actual document content."""

    @patch("rag.nodes.grade_documents_chain")
    def test_preserves_document_metadata(self, mock_chain):
        """Test that document metadata is preserved through grading."""
        from rag.nodes import grade_documents

        doc = RetrievedDocument(
            content="Test content about Python",
            source_name="python_guide.pdf",
            source_page=42,
            score=0.95,
            retrieved_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        mock_chain.return_value = create_mock_grade(relevant=True, overall_score=0.85)

        state: RAGState = {
            "question": "Python question",
            "retrieved_documents": [doc],
        }

        result = grade_documents(state)

        result_doc = result["retrieved_documents"][0]
        assert result_doc.content == "Test content about Python"
        assert result_doc.source_name == "python_guide.pdf"
        assert result_doc.source_page == 42
        assert result_doc.score == 0.95
        assert result_doc.retrieval_grade is not None
        assert result_doc.retrieval_grade.review.overall_score == 0.85

    @patch("rag.nodes.grade_documents_chain")
    def test_each_document_graded_individually(self, mock_chain, sample_documents):
        """Test that grade_documents_chain is called once per document."""
        from rag.nodes import grade_documents

        mock_chain.return_value = create_mock_grade(relevant=True, overall_score=0.7)

        state: RAGState = {
            "question": "Test question",
            "retrieved_documents": sample_documents,
        }

        grade_documents(state)

        assert mock_chain.call_count == len(sample_documents)

