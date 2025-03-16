import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
embedding_model = "text-embedding-3-small"

def get_embeddings(texts):
    """Fetches embeddings for the given list of text inputs."""
    response = client.embeddings.create(
        model=embedding_model,
        input=texts  # Input is a list of text strings to get embeddings for
    )
    return [item.embedding for item in response.data]  # Extracts embeddings from response

def cosine_similarity(vec1, vec2):
    """Computes cosine similarity between two vectors to measure question similarity."""
    vec1, vec2 = np.array(vec1), np.array(vec2)  # Convert to NumPy arrays
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))  # Standard cosine similarity formula

# Accepts either a JSON-formatted string or python list.  It outputs a python list.
def remove_duplicates(questions, threshold=0.90):
    """
    Identifies and removes duplicate questions based on semantic similarity using embeddings.
    
    Parameters:
    - questions (list or str): A one-dimensional JSON array of strings, either as a Python list 
      or a JSON-formatted string.
    - threshold (float): Similarity threshold above which a question is considered a duplicate.
    
    Returns:
    - List of unique questions with duplicates removed.
    """
    # If the input is a JSON string, parse it into a Python list.
    if isinstance(questions, str):
        try:
            questions = json.loads(questions)
        except Exception as e:
            raise ValueError("Invalid JSON input.") from e

    if not (isinstance(questions, list) and all(isinstance(q, str) for q in questions)):
        raise ValueError("Unsupported input format: Expected a list of strings.")

    embeddings = get_embeddings(questions)
    duplicate_indices = set()
    num_questions = len(embeddings)

    for i in range(num_questions):
        if i in duplicate_indices:
            continue
        for j in range(i + 1, num_questions):
            if j in duplicate_indices:
                continue
            if cosine_similarity(embeddings[i], embeddings[j]) > threshold:
                duplicate_indices.add(j)

    return [q for idx, q in enumerate(questions) if idx not in duplicate_indices]

if __name__ == "__main__":
    import argparse
    from create_questions import create_questions
    from category_prompt_helper import category_prompt_helper

    parser = argparse.ArgumentParser(description="Generate and remove duplicate trivia questions.")
    parser.add_argument("--category", help="Trivia category.")
    parser.add_argument("--num_questions", type=int, help="Number of questions.")
    args = parser.parse_args()

    category = args.category
    num_questions = args.num_questions

    # Call category_prompt_helper using the provided category
    prompt_nuance = category_prompt_helper(category)
    print(prompt_nuance)

    # Generate trivia questions using the prompt nuance and given category
    questions = create_questions(category, num_questions, prompt_nuance)
    print("\nGenerated Trivia Questions:\n")
    print(questions)

    # Convert the JSON string into a Python list if necessary.
    if isinstance(questions, str):
        questions = json.loads(questions)

    # Remove duplicates
    unique_questions = remove_duplicates(questions)
    print("\nUnique Questions:\n")
    print(json.dumps(unique_questions, indent=2))
    print(f"\nTotal unique questions: {len(unique_questions)}")
    print(f"\nTotal original questions: {len(questions)}")