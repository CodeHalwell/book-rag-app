import sys
from pathlib import Path
import logging
import re
import tqdm
# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.getLogger("pypdf").setLevel(logging.ERROR) 

class DocumentLoader:
    def __init__(self, directory: str):
        self.directory = directory
        
    def load_documents(self) -> list[Document]:
        """Loads PDFs from the directory with error handling.
        
        Args:
            None
        Returns:
            A list of documents.
        """
        try:
            loader = PyPDFDirectoryLoader(self.directory, glob="**/*.pdf")
            documents = loader.load()
            print(f"Loaded {len(documents)} pages from {self.directory}")
            return documents
        except Exception as e:
            print(f"Error loading documents: {e}")
            return []

    def clean_text(self, text: str) -> str:
        """Cleans common PDF artifacts such as multiple newlines and excessive whitespace.
        
        Args:
            text: The text to clean.
        Returns:
            The cleaned text.
        """
        # Fix surrogate pairs (UnicodeEncodeError)
        text = text.encode('utf-8', 'ignore').decode('utf-8')
        
        # Remove NUL bytes which also cause issues
        text = text.replace('\x00', '')

        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def split_documents(self, documents: list[Document]) -> list[Document]:
        """Splits documents into overlapping chunks.
        
        Args:
            documents: The documents to split.
        Returns:
            The split documents.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        return text_splitter.split_documents(documents)

    def preprocess_documents(self) -> list[Document]:
        """Loads, cleans, and splits documents.
        
        Args:
            None
        Returns:
            A list of documents.
        """
        documents = self.load_documents()
        
        for doc in tqdm.tqdm(documents, desc="Cleaning documents"):
            doc.page_content = self.clean_text(doc.page_content)
            doc.metadata["source_file"] = Path(doc.metadata.get("source", "")).name

        split_documents = self.split_documents(documents)
        return split_documents
