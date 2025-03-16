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
Create a comprehensive guide for generating exceptional trivia questions in the category: '{category}'.

        Analyze the distinctive elements of '{category}' and develop specific guidelines that will help create engaging, accurate, and diverse trivia questions. Focus on:

        - Key knowledge domains within this category
        - Different question formats that work well
        - Types of facts that make for interesting questions
        - Ways to ensure questions are factually accurate

        Format your response using the exact structure below:

        ### {category} Trivia Question Guidelines

        **[Descriptive Guideline Title 1]**
        Clear explanation of the guideline.

        **[Descriptive Guideline Title 2]**
        Clear explanation of the guideline.

        [Continue with additional guidelines, maximum of 10 total]

        Important: Do not include guidelines about visual questions or difficulty balancing. Focus exclusively on content, format, and quality considerations for text-based trivia questions.
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