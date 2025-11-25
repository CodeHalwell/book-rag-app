import sys
from pathlib import Path
import os
import asyncio
import pandas as pd
import json
from dotenv import load_dotenv
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rag.graph import build_graph
from utils.logging import Logging

load_dotenv()
logging = Logging()
rag_graph = build_graph()

async def generate_answers(output_path: str):
    """
    The engine room for our evaluation.
    This script feeds questions from a CSV into our RAG pipeline, collects the answers
    and the documents we used, and saves it all for grading.
    """
    input_path = "evaluation/data/ragas_data.csv"
    if not os.path.exists(input_path):
        logging.log_error(f"Input file not found: {input_path}")
        print(f"Error: File not found at {input_path}")
        return

    logging.log_info(f"Loading questions from {input_path}")
    df = pd.read_csv(input_path)
    
    generated_answers = []
    all_contexts = []
    
    total = len(df)
    print(f"Starting answer generation for {total} questions...")

    for index, row in df.iterrows():
        question = row.get("Prompt")
        if not question or pd.isna(question):
            logging.log_error(f"Row {index} is missing 'Prompt'")
            generated_answers.append("")
            all_contexts.append("[]")
            continue
            
        print(f"Processing {index + 1}/{total}...")
        logging.log_info(f"Processing question {index + 1}/{total}: {str(question)[:50]}...")
        
        try:
            # Invoke RAG graph
            # Here we go! Sending the question into the machine.
            res = await rag_graph.ainvoke({"question": question})
            answer = res.get("answer", "No answer generated")
            
            generated_answers.append(answer)
            
            # Extract contexts
            # We need to know exactly what texts the model looked at to generate the answer.
            docs = res.get("retrieved_documents", [])
            current_contexts = []
            for d in docs:
                if isinstance(d, str):
                    current_contexts.append(d)
                elif isinstance(d, dict):
                    current_contexts.append(d.get("content", ""))
                elif hasattr(d, "content"):
                    current_contexts.append(d.content)
                else:
                    current_contexts.append(str(d))
            
            # Store as JSON string to preserve list structure in CSV
            all_contexts.append(json.dumps(current_contexts))
            
        except Exception as e:
            logging.log_error(f"Error processing question '{question}': {str(e)}")
            generated_answers.append(f"Error: {str(e)}")
            all_contexts.append("[]")

    # Add new columns
    df["generated_answer"] = generated_answers
    df["contexts"] = all_contexts

    output_file = f"{output_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSuccess! Generated answers and contexts saved to: {output_file}")
    logging.log_info(f"Saved results with generated answers and contexts to {output_file}")
    return output_file