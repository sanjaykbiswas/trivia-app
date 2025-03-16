import os
import sys
from pathlib import Path

# Add the project root to the Python path so we can import modules
# Adjust this path to the root of your project
project_root = Path("/Users/sanjaybiswas/development/trivia-app")  # Update this to match your path
sys.path.append(str(project_root))

from config.llm_config import LLMConfigFactory
from utils.question_generator.difficulty_helper import DifficultyHelper
from utils.question_generator.generator import QuestionGenerator

def test_difficulty_helper():
    """Test the updated DifficultyHelper implementation"""
    print("==== Testing Updated DifficultyHelper ====")
    
    # Create configurations
    config = LLMConfigFactory.create_default()
    
    # Initialize the helpers
    difficulty_helper = DifficultyHelper(config)
    
    # Test getting difficulty tiers
    print("\n--- Getting difficulty tiers for 'History' ---")
    try:
        difficulty_tiers = difficulty_helper.generate_difficulty_guidelines("History")
        
        # Print each tier
        for tier_name, description in difficulty_tiers.items():
            print(f"\n{tier_name}:")
            print(f"{description}")
        
        # Test getting a specific tier
        print("\n--- Getting specific tier ---")
        medium_tier = difficulty_helper.get_difficulty_by_tier(difficulty_tiers, "Medium")
        print("Medium tier description:", medium_tier)
        
        # Test getting by tier number
        tier3 = difficulty_helper.get_difficulty_by_tier(difficulty_tiers, 3)
        print("Tier 3 description:", tier3)
        
    except Exception as e:
        print(f"Error generating difficulty tiers: {e}")

def test_question_generator_with_difficulty():
    """Test the updated QuestionGenerator with difficulty levels"""
    print("\n==== Testing QuestionGenerator with Difficulty ====")
    
    # Create configurations
    config = LLMConfigFactory.create_default()
    
    # Initialize the generator
    question_generator = QuestionGenerator(config)
    
    # Test generating questions with different difficulty levels
    categories = ["Science", "History"]
    difficulties = ["Easy", "Hard"]
    
    for category in categories:
        for difficulty in difficulties:
            print(f"\n--- Generating {difficulty} questions for {category} ---")
            try:
                questions = question_generator.generate_questions(
                    category=category,
                    count=2,
                    difficulty=difficulty
                )
                
                print(f"Generated {len(questions)} questions:")
                for i, q in enumerate(questions, 1):
                    print(f"{i}. {q.content}")
                    
            except Exception as e:
                print(f"Error generating questions: {e}")

if __name__ == "__main__":
    test_difficulty_helper()
    test_question_generator_with_difficulty()