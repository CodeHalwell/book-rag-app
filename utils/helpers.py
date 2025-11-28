"""Utility helper functions."""
import re


def format_document_name(filename: str) -> str:
    """
    Convert a document filename into a readable title.
    
    Examples:
        'developingappswithgpt-4andchatgpt.pdf' -> 'Developing Apps with GPT-4 and ChatGPT'
        'aiengineering.pdf' -> 'AI Engineering'
    """
    if not filename:
        return filename
    
    # Remove file extension
    name = re.sub(r'\.[^.]+$', '', filename)
    
    # Lowercase for easier matching
    name = name.lower()
    
    # Dictionary of words to find and their proper capitalization
    # Order matters - longer/specific patterns first
    word_map = [
        # Special compound terms
        ('chatgpt', 'ChatGPT'),
        ('openai', 'OpenAI'),
        ('langchain', 'LangChain'),
        
        # DALL-E patterns
        ('dall-e-3', 'DALL-E 3'),
        ('dall-e-2', 'DALL-E 2'),
        ('dall-e3', 'DALL-E 3'),
        ('dall-e2', 'DALL-E 2'),
        ('dalle-3', 'DALL-E 3'),
        ('dalle-2', 'DALL-E 2'),
        ('dalle3', 'DALL-E 3'),
        ('dalle2', 'DALL-E 2'),
        ('dall-e', 'DALL-E'),
        ('dalle', 'DALL-E'),
        
        # GPT patterns
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5', 'GPT-3.5'),
        ('gpt-3', 'GPT-3'),
        ('gpt4o', 'GPT-4o'),
        ('gpt4', 'GPT-4'),
        ('gpt3', 'GPT-3'),
        
        # Acronyms
        ('ai', 'AI'),
        ('ml', 'ML'),
        ('nlp', 'NLP'),
        ('llm', 'LLM'),
        ('llms', 'LLMs'),
        ('api', 'API'),
        ('apis', 'APIs'),
        ('rag', 'RAG'),
        ('sql', 'SQL'),
        ('aws', 'AWS'),
        ('gcp', 'GCP'),
        
        # Common words (for splitting)
        ('engineering', ' Engineering '),
        ('developing', ' Developing '),
        ('generating', ' Generating '),
        ('unlocking', ' Unlocking '),
        ('applications', ' Applications '),
        ('solutions', ' Solutions '),
        ('creative', ' Creative '),
        ('generative', ' Generative '),
        ('intelligence', ' Intelligence '),
        ('artificial', ' Artificial '),
        ('building', ' Building '),
        ('designing', ' Designing '),
        ('learning', ' Learning '),
        ('machine', ' Machine '),
        ('secrets', ' Secrets '),
        ('images', ' Images '),
        ('prompts', ' Prompts '),
        ('prompt', ' Prompt '),
        ('cloud', ' Cloud '),
        ('apps', ' Apps '),
        ('with', ' with '),
        ('from', ' from '),
        ('and', ' and '),
        ('the', ' the '),
        ('for', ' for '),
        ('of', ' of '),
    ]
    
    # Apply replacements
    for pattern, replacement in word_map:
        name = name.replace(pattern, replacement)
    
    # Clean up: remove extra spaces, capitalize first letter of each word except small words
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Split into words
    words = name.split()
    
    # Process words
    result_words = []
    for i, word in enumerate(words):
        # Skip already formatted special terms
        if word in ['ChatGPT', 'OpenAI', 'LangChain', 'DALL-E', 'AI', 'ML', 'NLP', 
                    'LLM', 'LLMs', 'API', 'APIs', 'RAG', 'SQL', 'AWS', 'GCP'] or word.startswith('GPT-') or word.startswith('DALL-E'):
            result_words.append(word)
        # Small words stay lowercase unless first
        elif word.lower() in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from']:
            if i == 0:
                result_words.append(word.capitalize())
            else:
                result_words.append(word.lower())
        # Capitalize other words
        else:
            result_words.append(word.capitalize())
    
    return ' '.join(result_words)
