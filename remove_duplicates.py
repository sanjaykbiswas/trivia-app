import json
import os
import openai
import numpy as np
from dotenv import load_dotenv

# Set up OpenAI API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OPENAI_API_KEY found in .env file")

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Choose the embedding model
embedding_model = "text-embedding-3-small"  # Using a lightweight model for efficiency


def get_embeddings(texts):
    """Fetches embeddings for the given list of text inputs."""
    response = client.embeddings.create(
        model=embedding_model,  # Calls OpenAI embedding model
        input=texts  # Input is a list of text strings to get embeddings for
    )
    return [item.embedding for item in response.data]  # Extracts embeddings from response


def cosine_similarity(vec1, vec2):
    """Computes cosine similarity between two vectors to measure question similarity."""
    vec1, vec2 = np.array(vec1), np.array(vec2)  # Convert to NumPy arrays
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))  # Standard cosine similarity formula


def remove_duplicates(questions, threshold=0.90):
    """
    Identifies and removes duplicate questions based on semantic similarity using embeddings.
    
    Parameters:
    - questions (list): List of trivia question dictionaries.
    - threshold (float): Similarity threshold above which a question is considered a duplicate.
    
    Returns:
    - List of unique questions with duplicates removed.
    """
    texts = [
        f"{q['Question']} | {q['Correct Answer']} | {', '.join(q['Incorrect Answer Array'])}"
        for q in questions
    ]  # Create a text representation of each question for embedding

    embeddings = get_embeddings(texts)  # Get embeddings for each question

    duplicate_indices = set()  # Stores indices of duplicate questions
    num_questions = len(embeddings)

    # Compare each question with all other questions
    for i in range(num_questions):
        if i in duplicate_indices:
            continue  # Skip already marked duplicates
        for j in range(i + 1, num_questions):
            if j in duplicate_indices:
                continue  # Skip already marked duplicates
            if cosine_similarity(embeddings[i], embeddings[j]) > threshold:
                duplicate_indices.add(j)  # Mark question as duplicate

    return [q for idx, q in enumerate(questions) if idx not in duplicate_indices]  # Keep only unique questions


if __name__ == "__main__":
    import argparse
    from generate_questions import get_trivia_questions

    parser = argparse.ArgumentParser(description="Generate and remove duplicate trivia questions.")
    parser.add_argument("--category", required=True)
    parser.add_argument("--num_questions", type=int, required=True)
    args = parser.parse_args()

    questions = get_trivia_questions(args.category, args.num_questions)  # Generate questions
    unique_questions = remove_duplicates(questions)  # Remove duplicates

    print(json.dumps(unique_questions, indent=2))  # Print final unique questions
    print(f"\nTotal unique questions: {len(unique_questions)}")