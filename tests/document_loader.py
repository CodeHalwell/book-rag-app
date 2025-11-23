"""Tests for document loader."""
from database.document_loader import DocumentLoader

def test_clean_text_removes_excessive_newlines():
    loader = DocumentLoader("test_docs")
    result = loader.clean_text("Hello\n\n\n\nWorld")
    assert result == "Hello\n\nWorld"

def test_clean_text_removes_nul_bytes():
    loader = DocumentLoader("test_docs")
    result = loader.clean_text("Hello\x00World")
    assert result == "HelloWorld"

def test_clean_text_normalizes_whitespace():
    loader = DocumentLoader("test_docs")
    result = loader.clean_text("Hello    World")
    assert result == "Hello World"

def test_clean_text_handles_unicode():
    loader = DocumentLoader("test_docs")
    text = "Hello 世界"
    result = loader.clean_text(text)
    assert result == "Hello 世界"

def test_clean_text_strips_leading_trailing():
    loader = DocumentLoader("test_docs")
    result = loader.clean_text("  Hello World  ")
    assert result == "Hello World"