import sys
from pathlib import Path
import os
# Add project root to Python path when running directly
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts.retrieval_question import RETRIEVAL_QUESTION_SYSTEM_PROMPT
from prompts.grade_documents import GRADE_DOCUMENTS_SYSTEM_PROMPT
from prompts.generate_answer import GENERATE_ANSWER_SYSTEM_PROMPT, GENERATE_ANSWER_NO_DOCS_SYSTEM_PROMPT
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
    reasoning_effort="minimal",
    streaming=True,
)
logging.log_info("LLMs initialised.")

def retrieval_required_chain(question: str) -> str:
    """
    Decides if we need to fetch docs.
    It's essentially asking: "Do I know this off the top of my head, or do I need to look it up?"
    
    Args:
        question: The user's burning question.
    Returns:
        A RetrievalRequired object (yes/no and maybe an improved question).
    """

    logging.log_info("Initialising retrieval required chain...")
    retrieval_question_prompt = ChatPromptTemplate.from_messages([
        ("system", RETRIEVAL_QUESTION_SYSTEM_PROMPT),
        ("user", "{question}"),
    ])

    llm_structured_output = retrieval_required_llm.with_structured_output(RetrievalRequired)

    retrieval_question_chain = retrieval_question_prompt | llm_structured_output
    return retrieval_question_chain.invoke({"question": question})

def grade_documents_chain(question: str, retrieved_documents: list[str]) -> RetrievalGrade:
    """
    Grades the documents we found (synchronous version).
    We don't want to feed garbage to the LLM, so we filter out the irrelevant stuff here.
    
    Args:
        question: What the user asked.
        retrieved_documents: The raw text chunks we found.
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
    chain = grade_documents_prompt | llm_structured_output
    return chain.invoke({"question": question, "retrieved_documents": retrieved_documents})


async def grade_documents_chain_async(question: str, retrieved_documents: list[str]) -> RetrievalGrade:
    """
    Grades the documents we found (async version for parallel execution).
    
    Args:
        question: What the user asked.
        retrieved_documents: The raw text chunks we found.
    Returns:
        A RetrievalGrade object.
    """
    grade_documents_prompt = ChatPromptTemplate.from_messages([
        ("system", GRADE_DOCUMENTS_SYSTEM_PROMPT),
        ("user", "{question}"),
        ("user", "{retrieved_documents}"),
    ])
    llm_structured_output = document_grade_llm.with_structured_output(RetrievalGrade)
    chain = grade_documents_prompt | llm_structured_output
    return await chain.ainvoke({"question": question, "retrieved_documents": retrieved_documents})


def generate_answer_chain(question: str, retrieved_documents: list[dict], chat_history: list[dict] = None, callbacks: list = None) -> str:
    """
    The final step: crafting the answer.
    We take the question and the best docs we found, and ask the LLM to write a response.
    
    Args:
        question: The user's question.
        retrieved_documents: The chosen few documents that made the cut.
        chat_history: Previous conversation messages for context.
        callbacks: For streaming, if we're feeling fancy.
    Returns:
        The final answer string.
    """
    # Format documents for the prompt with source information
    logging.log_info("Formatting documents for the prompt...")
    
    # Build conversation history messages
    history_messages = []
    if chat_history:
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                history_messages.append(("human", content))
            else:
                history_messages.append(("assistant", content))
        logging.log_info(f"Including {len(chat_history)} messages of conversation history.")
    
    if retrieved_documents:
        documents_text = "\n\n".join([
            f"Document {i+1} [Source: {doc['source_name']}, Page: {doc['source_page']}]:\n{doc['content']}" 
            for i, doc in enumerate(retrieved_documents)
        ])
        messages = [
            ("system", GENERATE_ANSWER_SYSTEM_PROMPT),
            *history_messages,  # Include conversation history
            ("human", "{question}"),
            ("human", "Documents:\n{documents}"),
        ]
        generate_answer_prompt = ChatPromptTemplate.from_messages(messages)
        chain = generate_answer_prompt | answer_generation_llm
        logging.log_info("Answer generation chain initialised.")
        return chain.invoke({"question": question, "documents": documents_text}, config={"callbacks": callbacks})
    else:
        # No documents - just ask the question
        # Sometimes the user just says "hello", so we don't need to force-feed them documents.
        messages = [
            ("system", GENERATE_ANSWER_NO_DOCS_SYSTEM_PROMPT),
            *history_messages,  # Include conversation history
            ("human", "{question}"),
        ]
        generate_answer_prompt = ChatPromptTemplate.from_messages(messages)
        chain = generate_answer_prompt | answer_generation_llm
        logging.log_info("Answer generation chain initialised.")
        return chain.invoke({"question": question}, config={"callbacks": callbacks})

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