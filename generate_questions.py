import os
import argparse
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OPENAI_API_KEY found in .env file")

client = OpenAI(api_key=openai_api_key)
creation_llm = 'o1-preview'
json_llm = 'gpt-4o'

def generate_questions(category, num_questions):
    prompt = f"""
You are an expert trivia question generator capable of creating clever, thoughtful, interesting, and fun trivia questions across a wide range of topics. Your task is to produce {num_questions} trivia questions in the category "{category}".
Follow these detailed guidelines:

1. **Adaptability:**
   - Tailor the tone, style, and complexity of questions to fit the subject matter of "{category}".
   - For example, if "{category}" is a pop culture topic, questions can be lively, engaging, and humorous; if it’s academic, they should be clear, educational, and intellectually stimulating.

2. **Diversity of Difficulty:**
   - Provide questions with a range of difficulties, from easy to challenging.

3. **Diversity of Structure:**
   - **Standard Fact-Based Questions:** Straightforward questions with one correct answer (e.g., “What is the capital of France?”).
   - **Constraint or Pattern-Based Questions:** Questions that impose a specific condition on the answer (e.g., “Name a U.S. state whose name starts with the letter 'E'.”). Adjust constraints as needed to maintain accuracy.  If using these types of questions, ensure all the incorrect answers also start with the same letter so it's not obvious in a multiple choice scenario.
   - **Additional Styles:** Feel free to incorporate other question styles that promote creativity and engagement.  TRUE/FALSE is not allowed.

4. **Uniqueness:**
   - Ensure each question is unique with no duplicates, including semantic duplicates.

5. **Answers:**
   - Every question must include one correct answer and three distinct incorrect answers.
   - Verify that all answer choices are plausible, ensuring one clear correct answer.

6. **Output Format:**
   - Produce your output in valid JSON format.
   - The JSON for each question should contain the following fields:
     - **Category**
     - **Question**
     - **Correct Answer**
     - **Incorrect Answer Array: Incorrect Answer 1, Incorrect Answer 2, Incorrect Answer 3**. It is important that this field is named "Incorrect Answer Array", with the array of incorrect answers within.
     - **Difficulty**

7. **Answer Type:**
   - Ensure the questions and answers work well for both multiple choice and single response.  For example, if the question asks to list the first thing alphabetically and the answer format is multiple choice, the question would be too easy.

8. **Ineligible Characters**
   - Do not output \"The Prince\" 

Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is fun, thought-provoking, and formatted in valid JSON as specified.
    """
    messages = [
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=creation_llm,
        messages=messages
    )

    return response

def ensure_valid_json_format(raw_output):
    """
    Passes the raw output through another LLM call to ensure the response is valid JSON.
    """
    json_format_prompt = f"""
The following text should be formatted as valid JSON. If it is not, please correct any issues and return only the valid JSON output without any additional commentary. Don't include any unnecessary markdown. Just the pure JSON output.

{raw_output}
"""
    messages = [
        {"role": "user", "content": json_format_prompt}
    ]
    json_response = client.chat.completions.create(
        model=json_llm,
        messages=messages
    )
    return json_response.choices[0].message.content

def is_json_complete(json_text):
    """
    Checks if the JSON text is complete and contains the required fields for each trivia question.
    """
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return False

    # Define the required keys that each question must have, using the actual key from the output.
    required_keys = ["Category", "Question", "Correct Answer", "Incorrect Answer Array", "Difficulty"]

    if isinstance(data, list):
        for item in data:
            if not all(key in item for key in required_keys):
                return False
    elif isinstance(data, dict):
        if not all(key in data for key in required_keys):
            return False
    else:
        return False

    return True

def get_trivia_questions(category, num_questions):
    """
    Generates trivia questions and returns valid JSON that can be further processed by other modules.
    If the JSON is invalid, the raw output is printed before raising an error.
    """
    # Generate questions using the first LLM action.
    result = generate_questions(category, num_questions)
    raw_text = result.choices[0].message.content  # Extract the generated text

    # Run the output through a second LLM action to ensure it is valid JSON.
    json_text = ensure_valid_json_format(raw_text)
    
    # Check for JSON completeness before returning.
    if not is_json_complete(json_text):
        print("Invalid JSON output detected:")
        print(json_text)
        raise ValueError("Final JSON response is incomplete or missing required fields.")
    
    print(json_text)
    return json_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate trivia questions.")
    parser.add_argument("--category", type=str, required=True, help="Trivia question category")
    parser.add_argument("--num_questions", type=int, required=True, help="Number of trivia questions to generate")
    args = parser.parse_args()

    try:
        output_json = get_trivia_questions(args.category, args.num_questions)
        print(output_json)
    except ValueError as e:
        print("Error:", e)