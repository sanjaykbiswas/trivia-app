import json
import os
import openai
import numpy as np
import datetime
from generate_questions import get_trivia_questions

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OPENAI_API_KEY found in .env file")

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Choose the embedding model
embedding_model = "text-embedding-3-small"  # Or "text-embedding-3-large" for better quality

# Generate the trivia questions JSON (as a string)
questions_json = get_trivia_questions(category, num_questions)

# Directly parse the JSON string into a Python list of dictionaries
questions_data = json.loads(questions_json)

# Assign a temporary unique questionID to each question (e.g., Q1, Q2, ...)
for idx, question in enumerate(questions_data):
    question['temp_questionID'] = f"Q{idx + 1}"

# Create a text representation for each question for embedding
texts_for_embedding = [
    (
        f"QuestionID: {question['temp_questionID']}\n"
        f"Category: {question['Category']}\n"
        f"Question: {question['Question']}\n"
        f"Correct Answer: {question['Correct Answer']}\n"
        f"Incorrect Answers: {', '.join(question['Incorrect Answer Array'])}\n"
        f"Difficulty: {question['Difficulty']}"
    )
    for question in questions_data
]

# Obtain embeddings for each question in a single batch API call
response = client.embeddings.create(
    model=embedding_model,
    input=texts_for_embedding
)

# Extract embeddings from the response
embeddings = [item.embedding for item in response.data]

# Define cosine similarity function
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Compare each embedding with others to detect duplicates
threshold = 0.90
num_questions = len(embeddings)

duplicate_indices = set()
duplicates_info = {}

for i in range(num_questions):
    if i in duplicate_indices:
        continue  # Skip questions already marked as duplicates
    for j in range(i + 1, num_questions):
        if j in duplicate_indices:
            continue
        sim = cosine_similarity(embeddings[i], embeddings[j])
        if sim > threshold:
            duplicate_indices.add(j)
            original_id = questions_data[i]['temp_questionID']
            dup_id = questions_data[j]['temp_questionID']
            duplicates_info.setdefault(original_id, []).append(dup_id)

# Log duplicate questions detected
print("Duplicate questions detected:")
if duplicates_info:
    for original, dup_list in duplicates_info.items():
        print(f"Original QuestionID: {original} has duplicates: {', '.join(dup_list)}")
else:
    print("No duplicates found.")

# Remove duplicates, keeping only the first occurrence of each duplicate group.
unique_questions = [
    question for idx, question in enumerate(questions_data) if idx not in duplicate_indices
]

print("\nUnique questions kept:")
for question in unique_questions:
    print(f"{question['temp_questionID']}: {question['Question']}")

print(f"\nTotal unique questions kept: {len(unique_questions)}")

# ----------------------------------------------------------------------
# Transform unique questions to match the Supabase schema
# ----------------------------------------------------------------------
questions_for_supabase = [
    {
        "question_text": question["Question"],
        "difficulty": question["Difficulty"],
        "user_id": None,  # Leave as NULL in the database
        "created_at": datetime.datetime.utcnow().isoformat(),
        "correct_answer": question["Correct Answer"],
        "incorrect_answer_array": question["Incorrect Answer Array"]
    }
    for question in unique_questions
]

# Now you can pass `questions_for_supabase` to your Supabase batch upload process
print("\nQuestions ready for Supabase upload:")
print(json.dumps(questions_for_supabase, indent=2))