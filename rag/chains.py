import sys
from pathlib import Path
import os
# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from prompts.retrieval_question import RETRIEVAL_QUESTION_SYSTEM_PROMPT
from prompts.grade_documents import GRADE_DOCUMENTS_SYSTEM_PROMPT
from prompts.generate_answer import GENERATE_ANSWER_SYSTEM_PROMPT
from schema.models import RetrievalRequired, RetrievalGrade

from dotenv import load_dotenv
load_dotenv()

retrieval_required_llm = ChatOpenAI(
    model=os.getenv("RETRIEVAL_REQUIRED_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="minimal",
)

document_grade_llm = ChatOpenAI(
    model=os.getenv("DOCUMENT_GRADE_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="medium",
)
answer_generation_llm = ChatOpenAI(
    model=os.getenv("ANSWER_GENERATE_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="medium",
)

def retrieval_required_chain(question: str) -> str:
    """Retrieves the required documents for the question.
    
    Args:
        question: The question to retrieve the required documents for.
    Returns:
        A RetrievalRequired object.
    """

    retrieval_question_prompt = ChatPromptTemplate.from_messages([
        ("system", RETRIEVAL_QUESTION_SYSTEM_PROMPT),
        ("user", "{question}"),
    ])

    llm_structured_output = retrieval_required_llm.with_structured_output(RetrievalRequired)

    retrieval_question_chain = retrieval_question_prompt | llm_structured_output
    return retrieval_question_chain.invoke({"question": question})

def grade_documents_chain(question: str, retrieved_documents: list[str]) -> str:
    """Grades the documents for the question.
    
    Args:
        question: The question to grade the documents for.
        retrieved_documents: The retrieved documents to grade.
    Returns:
        A RetrievalGrade object.
    """
    grade_documents_prompt = ChatPromptTemplate.from_messages([
        ("system", GRADE_DOCUMENTS_SYSTEM_PROMPT),
        ("user", "{question}"),
        ("user", "{retrieved_documents}"),
    ])
    llm_structured_output = document_grade_llm.with_structured_output(RetrievalGrade)
    grade_documents_chain = grade_documents_prompt | llm_structured_output
    return grade_documents_chain.invoke({"question": question, "retrieved_documents": retrieved_documents})


def generate_answer_chain(question: str, retrieved_documents: list[str]) -> str:
    """Generates an answer for the question.
    
    Args:
        question: The question to generate an answer for.
        retrieved_documents: The retrieved documents to generate an answer for.
    Returns:
        A string answer.
    """
    generate_answer_prompt = ChatPromptTemplate.from_messages([
        ("system", GENERATE_ANSWER_SYSTEM_PROMPT),
        ("user", "{question}"),
        ("user", "{retrieved_documents}"),
    ])
    generate_answer_chain = generate_answer_prompt | answer_generation_llm
    return generate_answer_chain.invoke({"question": question, "retrieved_documents": retrieved_documents})

if __name__ == "__main__":
    question = "Hello, What is the capital of France?"
    retrieved_documents = ["Once upon a time in Paris there was a beautiful girl named Marie. She was known for her kindness and her beautiful hair. One day, she met a prince who was also known for his kindness and his beautiful hair. They fell in love and got married. They lived happily ever after."]
    retrieval_required = retrieval_required_chain(question)
    grade_documents = grade_documents_chain(question, retrieved_documents)
    answer = generate_answer_chain(question, retrieved_documents)
    print(retrieval_required)
    print(grade_documents)
    print(answer)