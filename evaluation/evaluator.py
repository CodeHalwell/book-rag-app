import os
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from datasets import Dataset

def run_evaluation(questions: list[str], answers: list[str], contexts: list[list[str]], ground_truths: list[str] = None):
    """
    Runs RAGAS evaluation on a set of RAG outputs.
    
    Args:
        questions: List of questions.
        answers: List of answers.
        contexts: List of contexts.
        ground_truths: List of ground truths.
    Returns:
        A dictionary of evaluation results.
    """
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
    }
    if ground_truths:
        data["ground_truth"] = ground_truths
        
    dataset = Dataset.from_dict(data)

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))
    embeddings = OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL"), api_key=os.getenv("OPENAI_API_KEY"))

    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
    ]
    
    if ground_truths:
        metrics.append(context_recall)

    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
    )

    return results

