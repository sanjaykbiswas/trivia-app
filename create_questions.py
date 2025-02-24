import os
import json
import argparse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
llm = 'gpt-4o'
json_llm = 'gpt-4o'

def generate_question_json(category, num_questions): # Creates the raw questions based on the defined guidelines.
    """ Calls OpenAI API to generate trivia questions. """

    prompt = f"""
    Generate {num_questions} trivia questions for the category '{category}'.  Ensure each question is unique.
    
    Follow these guidelines when creating a response:

    **Output format**
    -- Output the answers in valid JSON format.
    -- Output the questions only, no answers.
    -- No fluff, introductions, finishes.  Only questions.
    -- Do not number the questions.

    **Question Style**
    -- Trivia style, but keep the question style somewhat diverse so it is not monotonous.
    -- Create questions that are suitable for multiple-choice trivia answers (e.g., the correct answer should not be a paragraph long)
    -- Do not do riddles.

    **Adaptability**
    -- Tailor the tone, style, and complexity of questions to fit the subject matter of "{category}".
    -- For example, if "{category}" is a pop culture topic, questions can be lively, engaging, and humorous; if it is academic, they should be clear, educational, and intellectually stimulating.

    **Difficulty**
    -- Provide questions with a range of difficulties, but overall lean towards more challenging.

    Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is unique, fun, thought-provoking, and follows the above guidelines.
    """

    response = client.chat.completions.create(
        model=llm,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content

def ensure_valid_json_format(raw_output): # Checks that the output is in JSON format, and fixes it if not.
    """ Uses LLM to validate JSON format. """
    json_format_prompt = f"""
    Format the following text as valid JSON.
    
    If it is not, please correct any issues and return only the valid JSON output without any additional commentary. 
    
    Don't include any unnecessary markdown. Just the pure JSON output.'\n\n{raw_output}
    """
    response = client.chat.completions.create(
        model=json_llm,
        messages=[{"role": "user", "content": json_format_prompt}]
    )
    return response.choices[0].message.content

def create_formatted_questions(category, num_questions): # Returns a formatted JSON of questions.
    """ Generates and validates trivia questions JSON. """
    raw_text = generate_question_json(category, num_questions)
    json_validated_text = ensure_valid_json_format(raw_text)

    return json.loads(json_validated_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate trivia questions.")
    parser.add_argument("--category", required=True, help="Trivia category")
    parser.add_argument("--num_questions", type=int, required=True, help="Number of questions")

    args = parser.parse_args()
    result = create_formatted_questions(args.category, args.num_questions)

    print(json.dumps(result, indent=2)) # Prints the list of questions generated.
    print(f"\nTotal unique questions: {len(result)}")