import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bookrag.db')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    VECTOR_STORE_NAME = os.getenv('VECTOR_STORE_NAME')
    VECTOR_STORE_DB_PATH = os.getenv('VECTOR_STORE_DB_PATH')
    VECTOR_STORE_DOCUMENTS_DIRECTORY = os.getenv('VECTOR_STORE_DOCUMENTS_DIRECTORY')
    RETRIEVAL_REQUIRED_LLM = os.getenv('RETRIEVAL_REQUIRED_LLM')
    DOCUMENT_GRADE_LLM = os.getenv('DOCUMENT_GRADE_LLM')
    ANSWER_GENERATE_LLM = os.getenv('ANSWER_GENERATE_LLM')
    CURRENT_STATE = os.getenv('CURRENT_STATE')