import os
import sys
from pathlib import Path

# Add the project root to the Python path so we can import modules
# Adjust this path to the root of your project
project_root = Path("/Users/sanjaybiswas/development/trivia-app/backend/src")
sys.path.append(str(project_root))

from config.llm_config import LLMConfigFactory
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from models.question import Question

def test_llm_factory():
    """Test the LLM factory pattern implementation"""
    print("==== Testing LLM Factory Pattern ====")
    
    # Test 1: Create default config
    print("\n--- Test 1: Create default config ---")
    default_config = LLMConfigFactory.create_default()
    print(f"Default provider: {default_config.get_provider()}")
    print(f"Default model: {default_config.get_model()}")
    
    # Test 2: Create Anthropic config
    print("\n--- Test 2: Create Anthropic config ---")
    anthropic_config = LLMConfigFactory.create_anthropic("claude-3-7-sonnet-20250219")
    print(f"Anthropic provider: {anthropic_config.get_provider()}")
    print(f"Anthropic model: {anthropic_config.get_model()}")
    
    # Test 3: Create OpenAI config
    print("\n--- Test 3: Create OpenAI config ---")
    openai_config = LLMConfigFactory.create_openai("gpt-3.5-turbo")
    print(f"OpenAI provider: {openai_config.get_provider()}")
    print(f"OpenAI model: {openai_config.get_model()}")
    
    # Test 4: Generate question with Anthropic
    print("\n--- Test 4: Generate question with Anthropic ---")
    try:
        question_generator = QuestionGenerator(anthropic_config)
        questions = question_generator.generate_questions("Science", count=1)
        print(f"Generated question: {questions[0].content}")
    except Exception as e:
        print(f"Error generating question with Anthropic: {e}")
    
    # Test 5: Generate answers with OpenAI
    print("\n--- Test 5: Generate answers with OpenAI ---")
    try:
        # Create a mock question
        mock_question = Question(
            content="What is the largest planet in our solar system?",
            category="Science"
        )
        mock_question.id = "test-id-123"
        
        answer_generator = AnswerGenerator(openai_config)
        answers = answer_generator.generate_answers([mock_question], "Science", batch_size=1)
        print(f"Generated answer: {answers[0].correct_answer}")
        print(f"Incorrect options: {answers[0].incorrect_answers}")
        print(f"Difficulty: {answers[0].difficulty}")
    except Exception as e:
        print(f"Error generating answer with OpenAI: {e}")

if __name__ == "__main__":
    test_llm_factory()