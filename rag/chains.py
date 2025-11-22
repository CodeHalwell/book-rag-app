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
from utils.logging import Logging

logging = Logging()

from dotenv import load_dotenv
load_dotenv()

logging.log_info("Initialising LLMs...")
retrieval_required_llm = ChatOpenAI(
    model=os.getenv("RETRIEVAL_REQUIRED_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="minimal",
)
logging.log_info("Document grade LLM initialised.")
document_grade_llm = ChatOpenAI(
    model=os.getenv("DOCUMENT_GRADE_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="medium",
)
logging.log_info("Answer generation LLM initialised.")
answer_generation_llm = ChatOpenAI(
    model=os.getenv("ANSWER_GENERATE_LLM"), 
    temperature=0, 
    api_key=os.getenv("OPENAI_API_KEY"),
    reasoning_effort="medium",
)
logging.log_info("LLMs initialised.")

def retrieval_required_chain(question: str) -> str:
    """Retrieves the required documents for the question.
    
    Args:
        question: The question to retrieve the required documents for.
    Returns:
        A RetrievalRequired object.
    """

    logging.log_info("Initialising retrieval required chain...")
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
    logging.log_info("Initialising grade documents chain...")
    grade_documents_prompt = ChatPromptTemplate.from_messages([
        ("system", GRADE_DOCUMENTS_SYSTEM_PROMPT),
        ("user", "{question}"),
        ("user", "{retrieved_documents}"),
    ])
    logging.log_info("Document grade LLM structured output initialised.")
    llm_structured_output = document_grade_llm.with_structured_output(RetrievalGrade)
    logging.log_info("Grade documents chain initialised.")
    grade_documents_chain = grade_documents_prompt | llm_structured_output
    return grade_documents_chain.invoke({"question": question, "retrieved_documents": retrieved_documents})


def generate_answer_chain(question: str, retrieved_documents: list[dict]) -> str:
    """Generates an answer for the question.
    
    Args:
        question: The question to generate an answer for.
        retrieved_documents: List of document dicts with 'content', 'source_name', and 'source_page' keys.
    Returns:
        A string answer.
    """
    # Format documents for the prompt with source information
    logging.log_info("Formatting documents for the prompt...")
    if retrieved_documents:
        documents_text = "\n\n".join([
            f"Document {i+1} [Source: {doc['source_name']}, Page: {doc['source_page']}]:\n{doc['content']}" 
            for i, doc in enumerate(retrieved_documents)
        ])
        messages = [
            ("system", GENERATE_ANSWER_SYSTEM_PROMPT),
            ("user", "{question}"),
            ("user", "Documents:\n{documents}"),
        ]
        generate_answer_prompt = ChatPromptTemplate.from_messages(messages)
        generate_answer_chain = generate_answer_prompt | answer_generation_llm
        logging.log_info("Answer generation chain initialised.")
        return generate_answer_chain.invoke({"question": question, "documents": documents_text})
    else:
        # No documents - just ask the question
        messages = [
            ("system", GENERATE_ANSWER_SYSTEM_PROMPT),
            ("user", "{question}"),
        ]
        generate_answer_prompt = ChatPromptTemplate.from_messages(messages)
        generate_answer_chain = generate_answer_prompt | answer_generation_llm
        logging.log_info("Answer generation chain initialised.")
        return generate_answer_chain.invoke({"question": question})

if __name__ == "__main__":
    question = "Hello, What is the capital of France?"
    retrieved_documents = [{
        "content": "Once upon a time in Paris there was a beautiful girl named Marie. She was known for her kindness and her beautiful hair. One day, she met a prince who was also known for his kindness and his beautiful hair. They fell in love and got married. They lived happily ever after.",
        "source_name": "example_story.pdf",
        "source_page": 1
    }]
    retrieval_required = retrieval_required_chain(question)
    grade_documents = grade_documents_chain(question, [doc["content"] for doc in retrieved_documents])
    answer = generate_answer_chain(question, retrieved_documents)
    print(retrieval_required)
    print(grade_documents)
    print(answer)