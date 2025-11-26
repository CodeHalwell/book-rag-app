from pydantic import BaseModel, Field
from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage
from datetime import datetime

class Review(BaseModel):
    relevance: float = Field(description="The relevance of the documents", ge=0, le=1)
    usefulness: float = Field(description="The usefulness of the documents", ge=0, le=1)
    accuracy: float = Field(description="The accuracy of the documents", ge=0, le=1)
    completeness: float = Field(description="The completeness of the documents", ge=0, le=1)
    clarity: float = Field(description="The clarity of the documents", ge=0, le=1)
    overall_score: float = Field(description="The overall score of the documents", ge=0, le=1)

class RetrievalGrade(BaseModel):
    review: Review = Field(description="The review of the documents")
    relevant: bool = Field(description="Whether the documents are relevant to the question or not")

class RetrievedDocument(BaseModel):
    content: str = Field(description="The content of the document")
    source_name: str = Field(description="The name of the source of the document")
    source_page: int = Field(description="The page number of the source of the document")
    score: float = Field(description="The score of the document")
    retrieved_at: datetime = Field(description="The date and time the document was retrieved")
    retrieval_grade: Optional[RetrievalGrade] = Field(default=None, description="The retrieval grade of the document")

class RetrievalRequired(BaseModel):
    retrieval_required: bool = Field(description="Whether a retrieval question is required to answer the user's question")
    inappropriate_question: bool = Field(description="Whether the question is inappropriate or not")
    improved_question: str = Field(description="An improved question that is appropriate and relevant to the user's question")

class ChatMessage(BaseModel):
    role: str = Field(description="The role of the message sender (user or assistant)")
    content: str = Field(description="The content of the message")

class RAGState(TypedDict, total=False):
    question: str
    retrieved_documents: list[RetrievedDocument]
    messages: list[BaseMessage]
    chat_history: list[ChatMessage]  # Conversation memory
    answer: str
    search_queries: list[str]
    retrieval_time: float
    retrieval_required: RetrievalRequired

