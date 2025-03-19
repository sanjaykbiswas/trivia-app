#!/usr/bin/env python3
"""
Timing test script for question generation
This script measures performance of create_complete_question_set
"""

import asyncio
import sys
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Now import the modules after the path is set
from config.environment import Environment
from utils.supabase_actions import SupabaseActions
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.question_repository import QuestionRepository
from services.question_service import QuestionService
from utils.logging_config import setup_logging

# Setup logging
logger = setup_logging(app_name="timing_test", log_level=logging.INFO)

# Create a custom timer class to track API calls
class APITimer:
    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        print(f"🚀 STARTING: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        print(f"✅ COMPLETED: {self.name} - Execution time: {duration:.2f} seconds")
        return False

async def setup_services():
    """Set up required services for testing"""
    print("📋 Setting up services...")
    
    # Set up environment and Supabase client
    env = Environment()
    
    # Create Supabase client
    import supabase
    client = supabase.create_client(
        supabase_url=env.get("supabase_url"),
        supabase_key=env.get("supabase_key")
    )
    
    # Initialize the repository and service
    question_repository = QuestionRepository(client)
    question_service = QuestionService(question_repository)
    
    return question_service

async def test_create_complete_question_set(
    question_service,
    category,
    count,
    deduplicate=True,
    batch_size=50,
    difficulties=None,
    user_id="00000000-0000-0000-0000-000000000000"
):
    """
    Test the create_complete_question_set function and measure performance
    """
    print("\n" + "="*80)
    print(f"📊 PERFORMANCE TEST: create_complete_question_set")
    print("="*80)
    print(f"🔍 Parameters:")
    print(f"  • Category: {category}")
    print(f"  • Count: {count}")
    print(f"  • Deduplicate: {deduplicate}")
    print(f"  • Batch Size: {batch_size}")
    print(f"  • Difficulties: {difficulties}")
    print(f"  • User ID: {user_id}")
    print("-"*80)
    
    overall_start_time = time.time()
    
    try:
        # Measure the entire process
        with APITimer("Complete question set generation (end-to-end)"):
            complete_questions = await question_service.create_complete_question_set(
                category=category,
                count=count,
                deduplicate=deduplicate,
                batch_size=batch_size,
                difficulties=difficulties,
                user_id=user_id
            )
        
        # Display results
        print("\n📝 RESULTS:")
        print(f"  • Total questions generated: {len(complete_questions)}")
        
        # Show distribution by difficulty
        difficulties_count = {}
        for cq in complete_questions:
            difficulty = cq.question.difficulty
            difficulties_count[difficulty] = difficulties_count.get(difficulty, 0) + 1
        
        print("  • Questions by difficulty:")
        for difficulty, count in difficulties_count.items():
            print(f"    - {difficulty}: {count}")
        
        # Sample of generated questions
        print("\n📚 SAMPLE QUESTIONS:")
        sample_size = min(3, len(complete_questions))
        for i in range(sample_size):
            cq = complete_questions[i]
            print(f"\n  Question {i+1}:")
            print(f"  • Content: {cq.question.content}")
            print(f"  • Difficulty: {cq.question.difficulty}")
            print(f"  • Correct Answer: {cq.answer.correct_answer}")
            print(f"  • Incorrect Answers: {cq.answer.incorrect_answers}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    overall_end_time = time.time()
    overall_duration = overall_end_time - overall_start_time
    
    print("\n⏱️ OVERALL TIMING SUMMARY:")
    print(f"  • Total execution time: {overall_duration:.2f} seconds")
    print(f"  • Average time per question: {overall_duration / count:.2f} seconds")
    print("="*80)
    
    return complete_questions

async def monkey_patch_services(question_service):
    """
    Monkey patch the service methods to add timing information
    This is done to track individual API calls within the service
    """
    # Store original methods
    original_generate_and_save = question_service.generate_and_save_questions
    original_generate_across = question_service.generate_questions_across_difficulties
    original_generate_for_difficulty = question_service._generate_questions_for_difficulty
    original_generate_answers = question_service.generate_answers_for_questions
    
    # Patch generate_and_save_questions
    async def patched_generate_and_save_questions(*args, **kwargs):
        with APITimer("generate_and_save_questions"):
            return await original_generate_and_save(*args, **kwargs)
    
    # Patch generate_questions_across_difficulties
    async def patched_generate_questions_across_difficulties(*args, **kwargs):
        with APITimer("generate_questions_across_difficulties"):
            return await original_generate_across(*args, **kwargs)
    
    # Patch _generate_questions_for_difficulty
    async def patched_generate_questions_for_difficulty(*args, **kwargs):
        # Extract difficulty from args (should be the third argument)
        difficulty = args[2] if len(args) > 2 else "Unknown"
        with APITimer(f"generate_questions_for_difficulty ({difficulty})"):
            return await original_generate_for_difficulty(*args, **kwargs)
    
    # Patch generate_answers_for_questions
    async def patched_generate_answers_for_questions(*args, **kwargs):
        with APITimer("generate_answers_for_questions"):
            return await original_generate_answers(*args, **kwargs)
    
    # Apply patches
    question_service.generate_and_save_questions = patched_generate_and_save_questions
    question_service.generate_questions_across_difficulties = patched_generate_questions_across_difficulties
    question_service._generate_questions_for_difficulty = patched_generate_questions_for_difficulty
    question_service.generate_answers_for_questions = patched_generate_answers_for_questions
    
    # Also patch the generator's methods
    original_generator_generate = question_service.generator.generate_questions
    
    def patched_generator_generate(*args, **kwargs):
        # Extract category and difficulty from args
        category = args[0] if len(args) > 0 else kwargs.get('category', 'Unknown')
        difficulty = args[2] if len(args) > 2 else kwargs.get('difficulty', 'Unknown')
        with APITimer(f"LLM API Call: generate_questions ({category}/{difficulty})"):
            return original_generator_generate(*args, **kwargs)
    
    question_service.generator.generate_questions = patched_generator_generate
    
    # Patch answer generator
    original_answer_generate = question_service.answer_generator.generate_answers
    
    def patched_answer_generate(*args, **kwargs):
        with APITimer("LLM API Call: generate_answers"):
            return original_answer_generate(*args, **kwargs)
    
    question_service.answer_generator.generate_answers = patched_answer_generate
    
    return question_service

async def interactive_test():
    """Interactive test function"""
    print("=" * 50)
    print("TIMING TEST FOR QUESTION GENERATION".center(50))
    print("=" * 50)
    
    # Set up services
    question_service = await setup_services()
    
    # Monkey patch to add timing
    question_service = await monkey_patch_services(question_service)
    
    # Get test parameters from user
    print("\nEnter test parameters (or press Enter for defaults):")
    
    category_input = input("Category (default: Science): ").strip()
    category = category_input if category_input else "Science"
    
    count_input = input("Number of questions (default: 5): ").strip()
    count = int(count_input) if count_input.isdigit() else 5
    
    deduplicate_input = input("Deduplicate questions? (y/n, default: y): ").strip().lower()
    deduplicate = deduplicate_input != 'n'
    
    difficulties_input = input("Difficulties (comma-separated, default: all): ").strip()
    difficulties = None  # Default is all difficulties
    if difficulties_input:
        difficulties = [d.strip() for d in difficulties_input.split(',')]
    
    # Run the test
    await test_create_complete_question_set(
        question_service=question_service,
        category=category,
        count=count,
        deduplicate=deduplicate,
        difficulties=difficulties
    )

if __name__ == "__main__":
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
