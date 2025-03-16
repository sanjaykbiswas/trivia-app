import os
from dotenv import load_dotenv
import json
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

# Function to process questions in batches
def create_answers(question_batch, category):
    prompt = f"""
You are a trivia expert tasked with enriching a set of trivia questions in the {category} category.

For each question provided, create a complete JSON object containing:
- The original question text (exactly as provided)
- The correct answer (verified for accuracy)
- Three plausible but incorrect answers that follow these guidelines:
  • All incorrect answers must belong to the same category/type as the correct answer
  • If the question has specific constraints (e.g., "Cities starting with B"), all incorrect answers must meet those same constraints
  • Incorrect answers should vary in difficulty to avoid making the correct answer obvious
  • Incorrect answers should be factually incorrect but believable to someone with moderate knowledge of the topic
- A difficulty rating ("Easy", "Medium", or "Hard") based on:
  • Easy: Common knowledge that most people would know
  • Medium: Knowledge that requires some familiarity with the subject
  • Hard: Specialized knowledge that only enthusiasts or experts would likely know

FORMAT REQUIREMENTS:
1. Return ONLY a JSON array of objects with no additional text
2. Include ALL {len(question_batch)} questions in your response
3. Follow this exact structure:

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

DO NOT include explanations, markdown formatting, or any text outside the JSON structure.

    Here is the list of questions:
    """ + "\n".join([f'- \"{q}\"' for q in question_batch])

    try: 
        if LLM_PROVIDER == "openai":
            response = client.chat.completions.create(
                model=llm,
                messages=[{"role": "user", "content": prompt}],
            )
            if response.choices:
                content = response.choices[0].message.content
                parsed_content = json.loads(content) if isinstance(content, str) else content
                return json.dumps(parsed_content, indent=2)  # Ensure JSON formatting
            return json.dumps([], indent=2)  # Return empty JSON array if no response

        elif LLM_PROVIDER == "anthropic":
            response = client.messages.create(
                model=llm,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from the TextBlock object
            if isinstance(response.content, list) and len(response.content) > 0:
                text_content = response.content[0].text  # Extract text from the first TextBlock
                parsed_content = json.loads(text_content) if isinstance(text_content, str) else text_content
                return json.dumps(parsed_content, indent=2)  # Ensure JSON formatting
            return json.dumps([], indent=2)  # Return empty JSON array if no response

    except Exception as e:
        print(f"Error processing batch: {e}")
        return json.dumps([], indent=2)
    
def batch_questions(questions, batch_size):
    """
    Splits the list of questions into smaller batches.
    """
    return [questions[i:i + batch_size] for i in range(0, len(questions), batch_size)]

if __name__ == "__main__":
    from create_questions import create_questions
    from category_prompt_helper import category_prompt_helper
    from remove_duplicates import remove_duplicates

    parser = argparse.ArgumentParser(description="Generate and remove duplicate trivia questions.")
    parser.add_argument("--category", help="Trivia category.")
    parser.add_argument("--num_questions", type=int, help="Number of questions.")
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