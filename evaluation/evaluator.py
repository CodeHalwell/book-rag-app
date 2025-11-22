import os
import asyncio
import pandas as pd
import json
import traceback
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    context_entity_recall,
    NoiseSensitivity,
    answer_relevancy,
    faithfulness,
    AspectCritic
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from dotenv import load_dotenv
from utils.logging import Logging
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()
logging = Logging()

# Define custom correctness metric using AspectCritic (returns 0 or 1)
correctness = AspectCritic(
    name="correctness",
    definition="""Evaluate correctness based on:
1. Key info presence from expected answer
2. Factual accuracy against context
3. Addressing the question
4. Accuracy of specific technical details
If the answer meets these criteria, return 1 (pass). Otherwise return 0 (fail).""",
    strictness=1,
)

# Define Noise Sensitivity metrics
noise_sensitivity_irrelevant = NoiseSensitivity(name="noise_sensitivity_irrelevant", mode="irrelevant")
noise_sensitivity_relevant = NoiseSensitivity(name="noise_sensitivity_relevant", mode="relevant")

async def run_evaluation():
    input_path = "evaluation/data/ragas_data_with_answers.csv"
    if not os.path.exists(input_path):
        logging.log_error(f"Input file not found: {input_path}")
        print(f"Error: File not found at {input_path}")
        return

    logging.log_info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Prepare dataset columns
    questions = df["Prompt"].astype(str).tolist()
    answers = df["generated_answer"].fillna("").astype(str).tolist()
    ground_truths = df["Expected Answer"].astype(str).tolist()
    
    # Parse contexts from JSON string
    contexts = []
    if "contexts" in df.columns:
        for c in df["contexts"]:
            try:
                if pd.isna(c):
                    contexts.append([])
                else:
                    # Ensure it's a list of strings
                    parsed = json.loads(str(c))
                    if isinstance(parsed, list):
                        contexts.append([str(p) for p in parsed])
                    else:
                        contexts.append([])
            except Exception as e:
                logging.log_error(f"Error parsing context: {e}")
                contexts.append([])
    else:
        logging.log_error("Contexts column missing in CSV!")
        contexts = [[] for _ in range(len(df))]
            
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "retrieved_contexts": contexts,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data)
    
    # Setup LLM and Embeddings
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Use LangchainLLMWrapper manually to ensure correct LLM type
    openai_model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
    llm = LangchainLLMWrapper(openai_model)
    
    # Use LangchainEmbeddingsWrapper manually
    openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    embeddings = LangchainEmbeddingsWrapper(openai_embeddings)
    
    print(f"LLM Type: {type(llm)}")
    print(f"Embeddings Type: {type(embeddings)}")
    
    metrics = [
        context_precision,
        context_recall,
        context_entity_recall,
        noise_sensitivity_irrelevant,
        noise_sensitivity_relevant,
        answer_relevancy,
        faithfulness,
        correctness
    ]
    
    logging.log_info("Starting Ragas evaluation with extended metrics...")
    print(f"Starting evaluation with {len(metrics)} metrics (this may take a few minutes)...")
    
    try:
        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False
        )
        
        # Save results
        result_df = results.to_pandas()
        output_path = "evaluation/results/ragas_results_final.csv"
        os.makedirs("evaluation/results", exist_ok=True)
        result_df.to_csv(output_path, index=False)
        
        print(f"Evaluation complete. Results saved to {output_path}")
        print("\nAverage Scores:")
        print(results)
        
        # Calculate pass rate for correctness (AspectCritic returns 1 for pass, 0 for fail)
        if "correctness" in result_df.columns:
            # Check if correctness column is numeric
            if pd.api.types.is_numeric_dtype(result_df["correctness"]):
                pass_count = result_df[result_df["correctness"] == 1].shape[0]
            else:
                # Fallback if it returned strings for some reason
                pass_count = result_df[result_df["correctness"].astype(str).isin(["1", "1.0", "pass"])].shape[0]
                
            total = len(result_df)
            pass_rate = (pass_count / total) * 100 if total > 0 else 0
            print(f"\nCorrectness Pass Rate: {pass_rate:.1f}% ({pass_count}/{total})")
            
    except Exception as e:
        print(f"Evaluation failed: {e}")
        traceback.print_exc()
        logging.log_error(f"Evaluation failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
