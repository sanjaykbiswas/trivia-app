import os
import json
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Initialize Supabase client
load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials.")

supabase: Client = create_client(supabase_url, supabase_key)

def upload_to_supabase(questions):
    """ Uploads trivia questions to the Supabase database. """
    formatted_questions = [
        {
            "question_text": q["Question"],
            "difficulty": q["Difficulty"].lower(),  # Ensure lowercase
            "user_id": None,
            "created_at": None,
            "correct_answer": q["Correct Answer"],
            "incorrect_answer_array": q["Incorrect Answer Array"]
        }
        for q in questions
    ]

    response = supabase.table("questions").insert(formatted_questions).execute()
    print("Batch upload response:", response)

if __name__ == "__main__":
    import argparse
    from remove_duplicates import remove_duplicates
    from generate_questions import get_trivia_questions

    parser = argparse.ArgumentParser(description="Generate, filter, and upload trivia questions.")
    parser.add_argument("--category", required=True)
    parser.add_argument("--num_questions", type=int, required=True)
    args = parser.parse_args()

    questions = get_trivia_questions(args.category, args.num_questions)
    unique_questions = remove_duplicates(questions)
    upload_to_supabase(unique_questions)