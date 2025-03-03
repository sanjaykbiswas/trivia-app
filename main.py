import json
from create_questions import create_questions
from category_prompt_helper import category_prompt_helper
from remove_duplicates import remove_duplicates
from create_answers import create_answers
from create_answers import batch_questions
from upload_questions import upload_to_supabase

category = "General Knowledge"
num_questions = 300
batch_size = 50

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
    answers_json = create_answers(batch)
    try:
        batch_answers = json.loads(answers_json)
        all_answers.extend(batch_answers)
    except Exception as e:
        print(f"Error parsing answers for a batch: {e}")

print("\nQuestions with Answers:\n")
print(json.dumps(all_answers, indent=2))

# Upload all answers to supabase
upload_to_supabase(all_answers)