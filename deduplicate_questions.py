import json
import numpy as np
from openai import OpenAI
import os
import pandas as pd
from dotenv import load_dotenv

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

def remove_duplicates(questions, threshold=0.90):
    """
    Identifies and removes duplicate questions based on semantic similarity using embeddings.
    
    Parameters:
    - questions (list): List of either strings or dictionaries containing trivia questions.
    - threshold (float): Similarity threshold above which a question is considered a duplicate.
    
    Returns:
    - List of unique questions with duplicates removed.
    """
    if isinstance(questions, list) and all(isinstance(q, dict) for q in questions):
        # Case: JSON array of dictionaries
        texts = [
            f"{q['Question']} | {q['Correct Answer']} | {', '.join(q['Incorrect Answer Array'])}"
            for q in questions
        ]
    elif isinstance(questions, list) and all(isinstance(q, str) for q in questions):
        # Case: JSON array of strings (just the questions)
        texts = questions
    else:
        raise ValueError("Unsupported input format: Expected list of strings or list of dictionaries.")

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

def load_questions_from_csv(csv_file, column_name="Question"):
    """Loads questions from a CSV file based on the given column name."""
    df = pd.read_csv(csv_file)
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in CSV file.")
    return df[column_name].dropna().tolist()  # Remove NaN values and return as a list

if __name__ == "__main__":
    import argparse
    from create_questions import create_formatted_questions

    parser = argparse.ArgumentParser(description="Generate and remove duplicate trivia questions.")
    parser.add_argument("--format", required=True, choices=["script", "csv"], help="Specify input format: script or csv.")
    parser.add_argument("--input", help="Input CSV file (only required for CSV mode).")
    parser.add_argument("--category", help="Trivia category (required for script mode).")
    parser.add_argument("--num_questions", type=int, help="Number of questions (required for script mode).")
    parser.add_argument("--column", default="question_text", help="Column name for questions (only for CSV mode).")
    
    args = parser.parse_args()

    # Handle input mode
    if args.format == "script": # python3 deduplicate_questions.py --format script --category "Science" --num_questions 10
        if not args.category or not args.num_questions:
            parser.error("--category and --num_questions are required in script mode.")
        questions = create_formatted_questions(args.category, args.num_questions)  # Generate questions from script

    elif args.format == "csv": # python3 deduplicate_questions.py --format csv --input my_questions.csv --column "trivia_question"
        if not args.input:
            parser.error("--input is required in csv mode.")
        questions = load_questions_from_csv(args.input, args.column)

    else:
        raise ValueError("Invalid format. Choose 'script' or 'csv'.")

    unique_questions = remove_duplicates(questions)  # Remove duplicates

    # Print results
    print(json.dumps(unique_questions, indent=2))  # Print final unique questions
    print(f"\nTotal unique questions: {len(unique_questions)}")
    print(f"\nTotal original questions: {len(questions)}")