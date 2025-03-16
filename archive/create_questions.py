import os
from dotenv import load_dotenv
import argparse
import anthropic
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Choose LLM Provider: openai, xai, or anthropic
LLM_PROVIDER = "anthropic"

if LLM_PROVIDER == "openai":
    client = OpenAI(api_key=OPENAI_API_KEY)
    llm = 'gpt-4o'

elif LLM_PROVIDER == "anthropic":
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    llm = "claude-3-7-sonnet-20250219"

else:
    raise ValueError("Invalid LLM provider. Choose 'openai', or 'anthropic'.")

# Creates a JSON-formatted string of questions
def create_questions(category, num_questions, category_prompt_nuance):
    """ Calls LLM to generate trivia questions. """

    prompt = f"""
    Generate {num_questions} trivia questions for the category '{category}'.  Ensure each question is unique.
    
    Follow these primary guidelines when creating a response:

    **Output format**
    -- Output the answers in valid JSON format.
    -- One-dimensional JSON array of strings.  Do not nest the questions under a key.
    -- No markdown, fluff, introductions, or finishes.
    -- Output the questions only, no answers.
    -- Do not number the questions.
    -- Example format below:

    [
      "Question?",
      "Question?",
      "Question?"
    ]

    **Question Style**
    -- Trivia style, but keep the question style somewhat diverse so it is not monotonous.
    -- Ensure questions are suitable for multiple-choice trivia answers (e.g., the correct answer should not be a paragraph long)
    -- Do not do riddles.

    **Difficulty**
    -- Provide questions with a range of difficulties, but overall lean towards more challenging.

    Additionally, ensure you follow the following more specific guidelienes for the category '{category}':

    {category_prompt_nuance}

    Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is unique, fun, thought-provoking, and follows the above guidelines.
    """

    if LLM_PROVIDER == "openai":
        response = client.chat.completions.create(
            model=llm,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    elif LLM_PROVIDER == "anthropic":
        response = client.messages.create(
            model=llm,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    else:
        raise ValueError("Invalid LLM provider. Choose 'openai' or 'anthropic'.")

if __name__ == "__main__":
    from category_prompt_helper import category_prompt_helper
    import json

    parser = argparse.ArgumentParser(description="Generate trivia questions for a given category.")
    parser.add_argument("--category", type=str, default="Science", help="The category for the trivia questions")
    parser.add_argument("--num_questions", type=int, default=5, help="Number of trivia questions to generate")
    args = parser.parse_args()

    category = args.category
    num_questions = args.num_questions

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
    
    print(f"\nTotal original questions: {len(questions)}")