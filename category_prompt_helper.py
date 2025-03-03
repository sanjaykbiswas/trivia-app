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

# Create a prompt that will give context to the trivia question generator in Create_Questions.py
def category_prompt_helper(category):
    """ Calls the selected LLM API to generate a prompt helper tailored to the category. """

    prompt = f"""
    Generate a prompt that will help a **Trivia Question Generator** LLM come up with interesting trivia questions for the category '{category}'.

    The prompt should consider the nuances of '{category}', and frame these nuances in a way that will help the **Trivia Question Generator** create high-quality questions.

    Return clear, labeled guidelines in the following format, and limit the number of guidelines you create to 10. Don't output anything but the format described below.

    Category Guidelines

    **Guideline 1** Description of guideline 1 (Replace **Guideline 1** with a label for the guideline)

    **Guideline 2** Description of guideline 2 (Replace **Guideline 2** with a label for the guideline)

    **Guideline N** Description of guideline N (Replace **Guideline N** with a label for the guideline)

    --
    None of the guidelines should involve visual question generation or difficulty balancing.
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
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    else:
        raise ValueError("Invalid LLM provider. Choose 'openai' or 'anthropic'.")

# Test the function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate trivia questions for a given category.")
    parser.add_argument("--category", type=str, default="Science", help="The category for the trivia questions")
    args = parser.parse_args()

    category = args.category
    
    prompt_nuance = category_prompt_helper(category)
    print(prompt_nuance)