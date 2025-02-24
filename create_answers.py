import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
llm = 'gpt-4o'

# Input JSON array of questions (fixed missing commas)
questions = [
    "What is the capital city of Australia?",
    "Which element has the chemical symbol 'O'?",
    "What year did the Titanic sink?",
    "Which planet is known as the Red Planet?",
    "Who wrote the play 'Romeo and Juliet'?",
    "In which country would you find the city of Timbuktu?",
    "What is the hardest natural substance on Earth?",
    "What is the national sport of Japan?",
    "Which is the smallest prime number?",
    "Who painted the Mona Lisa?",
] * 7  # Expanding to match your repeated list

# Function to process questions in batches
def generate_trivia_answers_batch(question_batch):
    prompt = f"""
    You are an expert at trivia. You will receive a list of multiple trivia questions.
    
    **For each question in the list, generate a separate JSON object.**

    Each object should include:
    - The correct answer.
    - Three plausible but incorrect answers.
    - A difficulty rating (Easy, Medium, or Hard).

    Return the response as a **JSON array of objects**, formatted like this:

    [
        {{
            "Question": "What is the capital of France?",
            "Correct Answer": "Paris",
            "Incorrect Answer Array": ["London", "Rome", "Berlin"],
            "Difficulty": "Easy"
        }},
        {{
            "Question": "Which planet is known as the Red Planet?",
            "Correct Answer": "Mars",
            "Incorrect Answer Array": ["Venus", "Jupiter", "Saturn"],
            "Difficulty": "Easy"
        }}
    ]

    **You MUST return all {len(question_batch)} questions in the response. Do NOT return just one question.**

    **Return only the pure JSON. No extra text, comments, or formatting like ```json.**

    Here is the list of questions:
    """ + "\n".join([f'- \"{q}\"' for q in question_batch])

    try:
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": "You are a trivia assistant. Always return ALL input questions as a JSON array."},
                {"role": "user", "content": prompt}
            ],
        )
        return json.loads(response.choices[0].message.content) if response.choices else None
    except Exception as e:
        print(f"Error processing batch: {e}")
        return None

# Process questions in batches of 50
batch_size = 50
all_responses = []

for i in range(0, len(questions), batch_size):
    batch = questions[i:i + batch_size]
    batch_response = generate_trivia_answers_batch(batch)

    if batch_response:
        all_responses.extend(batch_response)  # Collect all responses

# Save the final JSON output
output_file = "trivia_questions.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_responses, f, indent=4, ensure_ascii=False)

print(f"All questions processed and saved to {output_file}")