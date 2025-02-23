import os
import json
import csv
import argparse
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OPENAI_API_KEY found in .env file")

client = OpenAI(api_key=openai_api_key)
creation_llm = 'o1-preview'
json_llm = 'gpt-4o'

def generate_questions(category, num_questions):
    """ Calls OpenAI API to generate trivia questions. """
    prompt = f"""
You are an expert trivia question generator capable of creating clever, thoughtful, interesting, and fun trivia questions across a wide range of topics. Your task is to produce {num_questions} trivia questions in the category "{category}".  Ensure each question is unique with no duplicates, including semantic duplicates.
Follow these detailed guidelines:

1. **Adaptability:**
   - Tailor the tone, style, and complexity of questions to fit the subject matter of "{category}".
   - For example, if "{category}" is a pop culture topic, questions can be lively, engaging, and humorous; if it’s academic, they should be clear, educational, and intellectually stimulating.

2. **Diversity of Difficulty:**
   - Provide questions with a range of difficulties, either Easy, Medium, or Hard.

3. **Diversity of Structure:**
   - **Standard Fact-Based Questions:** Straightforward questions with one correct answer (e.g., “What is the capital of France?”).
   - **Constraint or Pattern-Based Questions:** Questions that impose a specific condition on the answer (e.g., “Name a U.S. state whose name starts with the letter 'E'.”). Adjust constraints as needed to maintain accuracy. If using these types of questions, ensure all the incorrect answers also start with the same letter so it's not obvious in a multiple choice scenario.
   - **Additional Styles:** Feel free to incorporate other question styles that promote creativity and engagement. TRUE/FALSE is not allowed.
   - **Riddles** Do not do riddles.
   
4. **Answers:**
   - Every question must include one correct answer and three distinct incorrect answers.
   - Verify that all answer choices are plausible, ensuring one clear correct answer.

5. **Output Format:**
   - Produce your output in valid JSON format.
   - The JSON for each question should contain the following fields:
     - **Category**
     - **Question**
     - **Correct Answer**
     - **Incorrect Answer Array**: ["Incorrect Answer 1", "Incorrect Answer 2", "Incorrect Answer 3"]
     - **Difficulty**

6. **Answer Type:**
   - Ensure the questions and answers work well for both multiple choice and single response.

7. **Ineligible Characters**
   - Do not output double quotations and wrap in 'The Prince', use single quotations instead.
   - Do not output the symbol for "degrees", use the word 'degrees' (e.g., 50 degrees Celsius).

8. **Question count**
   - Create {num_questions} unique questions

Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is fun, thought-provoking, and formatted in valid JSON as specified.
    """
    response = client.chat.completions.create(
        model=creation_llm,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def ensure_valid_json_format(raw_output):
    """ Uses LLM to validate JSON format. """
    json_format_prompt = f"Format the following text as valid JSON. If it is not, please correct any issues and return only the valid JSON output without any additional commentary. Don't include any unnecessary markdown. Just the pure JSON output.  The incorrect answer field should be formatted as 'Incorrect Answer Array'\n\n{raw_output}"
    response = client.chat.completions.create(
        model=json_llm,
        messages=[{"role": "user", "content": json_format_prompt}]
    )
    return response.choices[0].message.content

def is_json_complete(json_text):
    """
    Checks if the JSON text is complete and contains the required fields for each trivia question.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return False

    required_keys = ["Category", "Question", "Correct Answer", "Incorrect Answer Array", "Difficulty"]

    if isinstance(data, list):
        return all(all(key in item for key in required_keys) for item in data)
    elif isinstance(data, dict):
        return all(key in data for key in required_keys)
    
    return False

def get_trivia_questions(category, num_questions):
    """ Generates and validates trivia questions JSON. """
    raw_text = generate_questions(category, num_questions)
    json_text = ensure_valid_json_format(raw_text)

    # Validate JSON before returning
    if not is_json_complete(json_text):
        print("Invalid JSON output detected:")
        print(json_text)
        raise ValueError("Final JSON response is incomplete or missing required fields.")

    return json.loads(json_text)

def save_questions_to_csv(questions, filename="generated_trivia_questions.csv"):
    """ Saves questions to a CSV file. """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Category", "Question", "Correct Answer", "Incorrect Answer 1", "Incorrect Answer 2", "Incorrect Answer 3", "Difficulty"])

        for q in questions:
            writer.writerow([
                q["Category"],
                q["Question"],
                q["Correct Answer"],
                q["Incorrect Answer Array"][0],
                q["Incorrect Answer Array"][1],
                q["Incorrect Answer Array"][2],
                q["Difficulty"]
            ])
    
    print(f"Questions saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate trivia questions.")
    parser.add_argument("--category", required=True, help="Trivia category")
    parser.add_argument("--num_questions", type=int, required=True, help="Number of questions")
    args = parser.parse_args()

    try:
        questions = get_trivia_questions(args.category, args.num_questions)
        print(json.dumps(questions, indent=2))  # Print questions to console
        save_questions_to_csv(questions)  # Save to CSV if run from command line
    except ValueError as e:
        print("Error:", e)