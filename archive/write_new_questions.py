import os
import json
import argparse
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Initialize Supabase client
load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials.")

supabase: Client = create_client(supabase_url, supabase_key)

def upload_to_supabase(questions, category):
    """Uploads trivia questions to Supabase with the given category."""
    
    # Check if the category already exists
    result = supabase.table("categories").select("id").eq("name", category).execute()
    if result.data and len(result.data) > 0:
        category_id = result.data[0]["id"]
    else:
        # Insert new category if it does not exist
        insert_result = supabase.table("categories").insert({"name": category}).execute()
        if not insert_result.data:
            print("Error inserting category:", insert_result)
            return
        category_id = insert_result.data[0]["id"]

    # Format questions and include the category_id
    formatted_questions = [
        {
            "question_text": q["Question"],
            "difficulty": q["Difficulty"].lower(),  # Ensure lowercase
            "created_by": None,
            "created_at": None,
            "correct_answer": q["Correct Answer"],
            "incorrect_answer_array": q["Incorrect Answer Array"],
            "category_id": category_id  # Associate the question with its category
        }
        for q in questions
    ]

    # Insert questions into the questions table
    response = supabase.table("questions").insert(formatted_questions).execute()
    
    # Check for error by verifying if data was returned
    if not response.data:
        print("Upload Error:", response)
    else:
        print("Upload Successful")

if __name__ == "__main__":
    from create_questions import create_questions
    from category_prompt_helper import category_prompt_helper
    from remove_duplicates import remove_duplicates
    from create_answers import create_answers
    from create_answers import batch_questions

    parser = argparse.ArgumentParser(description="Generate, filter, and upload trivia questions.")
    parser.add_argument("--category", required=True)
    parser.add_argument("--num_questions", type=int, required=True)
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for processing questions when generating answers.")
    args = parser.parse_args()

    category = args.category
    num_questions = args.num_questions
    batch_size = args.batch_size

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

    # Batch the questions before passing them to create_answers.
    batches = batch_questions(unique_questions, batch_size)
    all_answers = []
    for batch in batches:
        answers_json = create_answers(batch, category)
        try:
            batch_answers = json.loads(answers_json)
            all_answers.extend(batch_answers)
        except Exception as e:
            print(f"Error parsing answers for a batch: {e}")

    print("\nQuestions with Answers:\n")
    print(json.dumps(all_answers, indent=2))

    # Upload all answers to supabase
    upload_to_supabase(all_answers, category)