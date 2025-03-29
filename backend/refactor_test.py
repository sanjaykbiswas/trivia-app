#!/usr/bin/env python3
"""
Test script for the refactored multi-difficulty question generation
This script tests generation of trivia questions across multiple difficulty levels
using the refactored service architecture
"""

import asyncio
import json
import sys
import os
import logging
import time
import traceback
from typing import Dict

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Now import the modules after the path is set
from config.environment import Environment
from services.refactored_question_service import RefactoredQuestionService
from repositories.question_repository import QuestionRepository
from repositories.category_repository import CategoryRepository
from repositories.base_repository_impl import BaseRepositoryImpl
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from config.llm_config import LLMConfigFactory
from utils.logging_config import setup_logging
from utils.question_generator.category_helper import CategoryHelper
from utils.question_generator.difficulty_helper import DifficultyHelper
from utils.category_utils import CategoryUtils
from models.category import CreatorType

# Setup logging
logger = setup_logging(app_name="refactor_test", log_level=logging.INFO)

# Monkey patch the question generator methods to show output
original_call_llm_for_questions = QuestionGenerator._call_llm_for_questions
def patched_call_llm_for_questions(self, category, count, category_guidelines, difficulty_context=""):
    print(f"\n======= Calling LLM for {count} {category} questions =======")
    print(f"Using model: {self.model} from provider: {self.provider}")
    
    raw_response = original_call_llm_for_questions(self, category, count, category_guidelines, difficulty_context)
    
    print(f"\n======= Raw LLM Response =======")
    print(raw_response[:500] + "..." if len(raw_response) > 500 else raw_response)
    print("================================\n")
    
    return raw_response

# Monkey patch CategoryHelper to show responses
original_generate_category_guidelines = CategoryHelper.generate_category_guidelines
def patched_generate_category_guidelines(self, category):
    print(f"\n======= Generating Category Guidelines for '{category}' =======")
    guidelines = original_generate_category_guidelines(self, category)
    print(f"\n======= Category Guidelines =======")
    print(guidelines)  # Print full guidelines without truncation
    print("================================\n")
    return guidelines

# Monkey patch DifficultyHelper to show responses
original_generate_difficulty_guidelines = DifficultyHelper.generate_difficulty_guidelines
def patched_generate_difficulty_guidelines(self, category, category_guidelines=None):
    print(f"\n======= Generating Difficulty Guidelines for '{category}' =======")
    guidelines = original_generate_difficulty_guidelines(self, category, category_guidelines)
    print(f"\n======= Difficulty Guidelines =======")
    print(json.dumps(guidelines, indent=2))
    print("================================\n")
    return guidelines

# Apply monkey patching
QuestionGenerator._call_llm_for_questions = patched_call_llm_for_questions
CategoryHelper.generate_category_guidelines = patched_generate_category_guidelines
DifficultyHelper.generate_difficulty_guidelines = patched_generate_difficulty_guidelines

async def setup_supabase():
    """Create Supabase client for testing"""
    import supabase
    env = Environment()
    client = supabase.create_client(
        supabase_url=env.get("supabase_url"),
        supabase_key=env.get("supabase_key")
    )
    return client

async def setup_question_service():
    """Set up refactored question service with all dependencies"""
    # Get Supabase client
    client = await setup_supabase()
    
    # Create repositories
    question_repository = QuestionRepository(client)
    category_repository = CategoryRepository(client)
    
    # Create LLM config and generators
    llm_config = LLMConfigFactory.create_default()
    question_generator = QuestionGenerator(llm_config)
    answer_generator = AnswerGenerator(llm_config)
    deduplicator = Deduplicator()
    
    # Create category utils with repository
    category_utils = CategoryUtils(category_repository)
    
    # Create and return refactored question service
    question_service = RefactoredQuestionService(
        question_repository=question_repository,
        question_generator=question_generator,
        answer_generator=answer_generator,
        deduplicator=deduplicator,
        category_repository=category_repository
    )
    
    return question_service, client

async def ensure_category_exists(category_name: str, category_utils: CategoryUtils):
    """
    Ensure the specified category exists in the database
    Creates it with SYSTEM creator type if it doesn't already exist
    
    Args:
        category_name (str): The name of the category to check/create
        category_utils (CategoryUtils): Category utilities
    
    Returns:
        bool: True if the category was created, False if it already existed
    """
    # Check if the category already exists
    category = await category_utils.get_category_by_name(category_name)
    
    if category:
        logger.info(f"Category '{category_name}' already exists with ID: {category.id}")
        print(f"Category '{category_name}' already exists in the database.")
        return False
    
    # Create the category with SYSTEM creator type
    try:
        category = await category_utils.get_or_create_category(
            name=category_name,
            creator_type=CreatorType.SYSTEM
        )
        if category:
            logger.info(f"Created category '{category_name}' with ID: {category.id}")
            print(f"✅ Created new category '{category_name}' in the database with SYSTEM creator.")
            return True
        else:
            logger.error(f"Failed to create category '{category_name}'")
            print(f"⚠️ Failed to create category '{category_name}'")
            return False
    except Exception as e:
        logger.error(f"Error creating category '{category_name}': {e}")
        print(f"⚠️ Failed to create category '{category_name}': {e}")
        return False

async def test_multi_difficulty_generation():
    """Test generating questions with multiple difficulty levels concurrently"""
    question_service, client = await setup_question_service()
    category_utils = CategoryUtils()
    category_utils.repository = CategoryRepository(client)
    
    # Get test parameters
    print("\nREFACTORED MULTI-DIFFICULTY QUESTION GENERATION")
    print("=" * 50)
    
    # Get category input
    category_name = input("Enter category (e.g., History, Science, Movies): ")
    if not category_name:
        category_name = "General Knowledge"
    
    # Ensure the category exists in the database
    await ensure_category_exists(category_name, category_utils)
    
    # Get difficulty counts
    difficulty_counts = {}
    print("\nEnter question counts for each difficulty (0 to skip):")
    for difficulty in ["Easy", "Medium", "Hard", "Expert", "Master"]:
        count_input = input(f"{difficulty}: ")
        try:
            count = int(count_input)
            if count > 0:
                difficulty_counts[difficulty] = count
        except ValueError:
            pass  # Skip if invalid
    
    if not difficulty_counts:
        print("No valid difficulties specified, using defaults...")
        difficulty_counts = {"Easy": 2, "Medium": 2}
    
    total_count = sum(difficulty_counts.values())
    print(f"\nGenerating {total_count} '{category_name}' questions across {len(difficulty_counts)} difficulty levels...")
    print(f"Difficulty distribution: {difficulty_counts}")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        result = await question_service.create_multi_difficulty_question_set(
            category=category_name,
            difficulty_counts=difficulty_counts,
            deduplicate=True
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Count total questions generated
        total_generated = sum(len(questions) for questions in result.values())
        
        print(f"Successfully generated {total_generated} questions in {elapsed_time:.2f} seconds")
        
        # Print summary for each difficulty
        for difficulty, questions in result.items():
            print(f"\n{difficulty} difficulty: {len(questions)} questions")
            if questions:
                # Show a sample question from each difficulty
                sample = questions[0]
                print(f"Sample: {sample.content}")
                print(f"Answer: {sample.correct_answer}")
                print(f"Incorrect options: {', '.join(sample.incorrect_answers)}")
        
        return True
    except Exception as e:
        print(f"Error during multi-difficulty generation: {e}")
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("=" * 60)
    print("REFACTORED MULTI-DIFFICULTY QUESTION GENERATION TEST".center(60))
    print("=" * 60)
    
    await test_multi_difficulty_generation()
    
    # Ask if the user wants to run another test
    again = input("\nRun another test? (y/n): ")
    if again.lower() == "y":
        await main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()
        sys.exit(1)