#!/usr/bin/env python3
"""
Manual test script for trivia app functionality
This script allows you to manually test various functionalities
with enhanced debugging for LLM responses
"""

import asyncio
import uuid
import json
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
from services.upload_service import UploadService
from services.question_service import QuestionService
from repositories.question_repository import QuestionRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator
from config.llm_config import LLMConfigFactory
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from utils.logging_config import setup_logging
from utils.question_generator.category_helper import CategoryHelper
from utils.question_generator.difficulty_helper import DifficultyHelper

# Setup logging
logger = setup_logging(app_name="manual_test", log_level=logging.INFO)

# Monkey patch the _call_llm_for_questions method to capture raw responses
original_call_llm_for_questions = QuestionGenerator._call_llm_for_questions
def patched_call_llm_for_questions(self, category, count, category_guidelines, difficulty_context=""):
    print(f"\n======= Calling LLM for {count} {category} questions =======")
    print(f"Using model: {self.model} from provider: {self.provider}")
    
    raw_response = original_call_llm_for_questions(self, category, count, category_guidelines, difficulty_context)
    
    print(f"\n======= Raw LLM Response =======")
    print(raw_response)
    print("================================\n")
    
    # Try parsing to catch errors early with better messages
    try:
        json.loads(raw_response)
        print("✅ Response is valid JSON")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        print("Attempting to fix JSON...")
        # Try to extract valid JSON from the response
        fixed_json = try_fix_json(raw_response)
        if fixed_json:
            print("✅ Fixed JSON successfully")
            return fixed_json
    
    return raw_response

# Monkey patch CategoryHelper to show responses
original_generate_category_guidelines = CategoryHelper.generate_category_guidelines
def patched_generate_category_guidelines(self, category):
    print(f"\n======= Generating Category Guidelines for '{category}' =======")
    guidelines = original_generate_category_guidelines(self, category)
    print(f"\n======= Category Guidelines =======")
    print(guidelines)
    print("================================\n")
    return guidelines

# Monkey patch DifficultyHelper to show responses
original_generate_difficulty_guidelines = DifficultyHelper.generate_difficulty_guidelines
def patched_generate_difficulty_guidelines(self, category):
    print(f"\n======= Generating Difficulty Guidelines for '{category}' =======")
    guidelines = original_generate_difficulty_guidelines(self, category)
    print(f"\n======= Difficulty Guidelines =======")
    print(json.dumps(guidelines, indent=2))
    print("================================\n")
    return guidelines

# Add monkey patching
QuestionGenerator._call_llm_for_questions = patched_call_llm_for_questions
CategoryHelper.generate_category_guidelines = patched_generate_category_guidelines
DifficultyHelper.generate_difficulty_guidelines = patched_generate_difficulty_guidelines

def try_fix_json(raw_text):
    """
    Attempt to extract or fix JSON from raw text
    """
    # Try to find JSON array in the response
    json_start = raw_text.find('[')
    json_end = raw_text.rfind(']')
    
    if json_start != -1 and json_end != -1:
        # Extract only the JSON array part
        json_text = raw_text[json_start:json_end+1]
        try:
            # Check if it's valid JSON
            json_data = json.loads(json_text)
            return json_data
        except json.JSONDecodeError:
            # Still not valid
            pass
    
    # Try more advanced fixes
    # 1. Replace common markdown formatting
    clean_text = raw_text.replace("```json", "").replace("```", "")
    
    # 2. Try to extract JSON array again
    json_start = clean_text.find('[')
    json_end = clean_text.rfind(']')
    
    if json_start != -1 and json_end != -1:
        json_text = clean_text[json_start:json_end+1]
        try:
            json_data = json.loads(json_text)
            return json_data
        except json.JSONDecodeError:
            # Still not valid
            pass
    
    # 3. Try to extract questions directly if JSON isn't working
    # Look for patterns like "Question?", with quotes
    import re
    questions = re.findall(r'"([^"]+\?)"', raw_text)
    if questions and len(questions) > 0:
        print(f"Extracted {len(questions)} questions using regex")
        return questions
    
    return None

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
    """Set up question service with all dependencies"""
    # Get Supabase client
    client = await setup_supabase()
    
    # Create repository
    question_repository = QuestionRepository(client)
    
    # Create LLM config and generators
    llm_config = LLMConfigFactory.create_default()
    question_generator = QuestionGenerator(llm_config)
    answer_generator = AnswerGenerator(llm_config)
    deduplicator = Deduplicator()
    
    # Create and return question service
    question_service = QuestionService(
        question_repository=question_repository,
        question_generator=question_generator,
        answer_generator=answer_generator,
        deduplicator=deduplicator
    )
    
    return question_service, client

async def test_single_difficulty_generation():
    """Test generating questions with a single difficulty level"""
    question_service, _ = await setup_question_service()
    
    # Get test parameters
    print("\nSINGLE DIFFICULTY QUESTION GENERATION")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
    difficulty = input("Enter difficulty (Easy, Medium, Hard, Expert, Master): ")
    if not difficulty:
        difficulty = "Medium"
    
    count = input("Number of questions to generate (1-100): ")
    try:
        count = int(count)
        if count < 1 or count > 100:
            count = 3
    except ValueError:
        count = 3
    
    print(f"\nGenerating {count} '{category}' questions with '{difficulty}' difficulty...")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        questions = await question_service.generate_and_save_questions(
            category=category,
            count=count,
            deduplicate=True,
            difficulty=difficulty
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print(f"Successfully generated {len(questions)} questions in {elapsed_time:.2f} seconds")
        
        # Summarize question data instead of showing all questions
        print(f"\nGenerated {len(questions)} questions with difficulty: {difficulty}")
        print(f"First few questions: {questions[0].content[:50]}...")
        if len(questions) > 1:
            print(f"Last question: {questions[-1].content[:50]}...")
        
        return True
    except Exception as e:
        print(f"Error during question generation: {e}")
        return False

async def test_async_question_generation():
    """Test generating questions using the concurrent async method"""
    # Get Supabase client and create repository
    client = await setup_supabase()
    question_repository = QuestionRepository(client)
    
    # Create LLM config directly
    llm_config = LLMConfigFactory.create_default()
    
    # Create the generators directly to access the async methods
    question_generator = QuestionGenerator(llm_config)
    
    # Get test parameters
    print("\nASYNC QUESTION GENERATION (CONCURRENT)")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
    difficulty = input("Enter difficulty (Easy, Medium, Hard, Expert, Master): ")
    if not difficulty:
        difficulty = "Medium"
    
    count = input("Number of questions to generate (1-100): ")
    try:
        count = int(count)
        if count < 1 or count > 100:
            count = 3
    except ValueError:
        count = 3
    
    print(f"\nGenerating {count} '{category}' questions with '{difficulty}' difficulty using async method...")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        # Generate questions using the async method
        if hasattr(question_generator, 'generate_questions_async'):
            questions = await question_generator.generate_questions_async(
                category=category,
                count=count,
                difficulty=difficulty
            )
        else:
            print("Async method not available, falling back to sync method")
            questions = question_generator.generate_questions(
                category=category,
                count=count,
                difficulty=difficulty
            )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print(f"Successfully generated {len(questions)} questions in {elapsed_time:.2f} seconds")
        
        # Save questions to database
        saved_questions = await question_repository.bulk_create(questions)
        
        # Summarize question data instead of showing all questions
        print(f"\nGenerated {len(saved_questions)} questions with difficulty: {difficulty}")
        print(f"First few questions: {saved_questions[0].content[:50]}...")
        if len(saved_questions) > 1:
            print(f"Last question: {saved_questions[-1].content[:50]}...")
        
        return True
    except Exception as e:
        print(f"Error during async question generation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_question_generation():
    """Test generating complete questions with answers"""
    question_service, _ = await setup_question_service()
    
    # Get test parameters
    print("\nCOMPLETE QUESTION GENERATION")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
    difficulty = input("Enter difficulty (Easy, Medium, Hard, Expert, Master): ")
    if not difficulty:
        difficulty = "Medium"
    
    count = input("Number of questions to generate (1-100): ")
    try:
        count = int(count)
        if count < 1 or count > 100:
            count = 3
    except ValueError:
        count = 3
    
    print(f"\nGenerating {count} '{category}' complete questions with '{difficulty}' difficulty...")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        complete_questions = await question_service.create_complete_question_set(
            category=category,
            count=count,
            deduplicate=True,
            difficulty=difficulty
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print(f"Successfully generated {len(complete_questions)} complete questions in {elapsed_time:.2f} seconds")
                
        # Summarize complete question data instead of showing all questions/answers
        print(f"\nGenerated {len(complete_questions)} complete questions with difficulty: {difficulty}")
        if len(complete_questions) > 0:
            print(f"First question: {complete_questions[0].content[:50]}...")
            print(f"First question answer: {complete_questions[0].correct_answer}")
        if len(complete_questions) > 1:
            print(f"Last question: {complete_questions[-1].content[:50]}...")
        
        return True
    except Exception as e:
        print(f"Error during complete question generation: {e}")
        # Add more detailed exception info
        import traceback
        traceback.print_exc()
        return False

async def test_async_complete_generation():
    """Test generating questions and answers using the async methods directly"""
    # Get Supabase client and create repository
    client = await setup_supabase()
    question_repository = QuestionRepository(client)
    
    # Create LLM config directly
    llm_config = LLMConfigFactory.create_default()
    
    # Create the generators directly to access the async methods
    question_generator = QuestionGenerator(llm_config)
    answer_generator = AnswerGenerator(llm_config)
    deduplicator = Deduplicator()
    
    # Get test parameters
    print("\nASYNC COMPLETE QUESTION GENERATION (CONCURRENT)")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
    difficulty = input("Enter difficulty (Easy, Medium, Hard, Expert, Master): ")
    if not difficulty:
        difficulty = "Medium"
    
    count = input("Number of questions to generate (1-100): ")
    try:
        count = int(count)
        if count < 1 or count > 100:
            count = 3
    except ValueError:
        count = 3
    
    print(f"\nGenerating {count} '{category}' complete questions with '{difficulty}' difficulty using async methods...")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        # Step 1: Generate questions asynchronously
        print("\nStep 1: Generating questions asynchronously...")
        if hasattr(question_generator, 'generate_questions_async'):
            questions = await question_generator.generate_questions_async(
                category=category,
                count=count,
                difficulty=difficulty
            )
        else:
            print("Async question method not available, falling back to sync method")
            questions = question_generator.generate_questions(
                category=category,
                count=count,
                difficulty=difficulty
            )
        
        # Optional deduplication if needed
        if hasattr(deduplicator, 'remove_duplicates'):
            questions = deduplicator.remove_duplicates(questions)
            
        # Save questions to database
        saved_questions = await question_repository.bulk_create(questions)
        
        print(f"Successfully generated and saved {len(saved_questions)} questions")
        
        # Step 2: Generate answers asynchronously
        print("\nStep 2: Generating answers asynchronously...")
        if hasattr(answer_generator, 'generate_answers_async'):
            answers = await answer_generator.generate_answers_async(
                questions=saved_questions,
                category=category
            )
        else:
            print("Async answer method not available, falling back to sync method")
            answers = answer_generator.generate_answers(
                questions=saved_questions,
                category=category
            )
        
        # Save answers to database
        saved_answers = await question_repository.bulk_save_answers(answers)
        
        # Create complete questions from questions and answers
        complete_questions = []
        answer_map = {a.question_id: a for a in saved_answers}
        
        for question in saved_questions:
            if question.id in answer_map:
                complete_question = CompleteQuestion(
                    question=question,
                    answer=answer_map[question.id]
                )
                complete_questions.append(complete_question)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        print(f"Successfully generated {len(complete_questions)} complete questions in {elapsed_time:.2f} seconds")
                
        # Summarize complete question data instead of showing all questions/answers
        print(f"\nGenerated {len(complete_questions)} complete questions with difficulty: {difficulty}")
        if len(complete_questions) > 0:
            print(f"First question: {complete_questions[0].content[:50]}...")
            print(f"First question answer: {complete_questions[0].correct_answer}")
        if len(complete_questions) > 1:
            print(f"Last question: {complete_questions[-1].content[:50]}...")
        
        return True
    except Exception as e:
        print(f"Error during async complete question generation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_creation():
    """Test creating a new user"""
    client = await setup_supabase()
    actions = SupabaseActions(client)
    
    # Generate a unique ID
    user_id = str(uuid.uuid4())
    
    # Check if user wants to create system user
    use_system_id = input("Create system user (00000000-0000-0000-0000-000000000000)? (y/n): ")
    if use_system_id.lower() == 'y':
        user_id = "00000000-0000-0000-0000-000000000000"
    
    # Get username from user
    username = input("Enter a username (or press Enter to use a generated one): ")
    if not username:
        if user_id == "00000000-0000-0000-0000-000000000000":
            username = "system"
        else:
            username = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"\nCreating user with ID {user_id} and username {username}...")
    
    # Create the user
    try:
        user_data = await actions.ensure_user_exists(user_id, username)
        print(f"User created successfully!")
        print(f"User data: {json.dumps(user_data, indent=2)}")
        return user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

async def test_question_upload(user_id=None):
    """Test uploading a question and answer"""
    client = await setup_supabase()
    upload_service = UploadService(client)
    
    # Get question details from user
    print("\nEnter question details:")
    content = input("Question: ")
    category = input("Category: ")
    correct_answer = input("Correct answer: ")
    
    # Get incorrect answers
    incorrect_answers = []
    print("Enter incorrect answers (enter empty line to finish):")
    while True:
        answer = input(f"Incorrect answer {len(incorrect_answers) + 1}: ")
        if not answer:
            break
        incorrect_answers.append(answer)
    
    # Get difficulty
    difficulty = input("Difficulty (Easy, Medium, Hard, Expert, Master): ")
    if not difficulty:
        difficulty = "Medium"
    
    # If no user_id provided, use the system user
    if not user_id:
        user_id = "00000000-0000-0000-0000-000000000000"
    
    print("\nUploading question...")
    
    # Upload the question
    try:
        result = await upload_service.upload_complete_question(
            question_content=content,
            category=category,
            correct_answer=correct_answer,
            incorrect_answers=incorrect_answers,
            difficulty=difficulty,
            user_id=user_id
        )
        
        print("Question uploaded successfully!")
        print(f"Question ID: {result.question.id}")
        print(f"Answer ID: {result.answer.id}")
        
        # Format the result for display
        display_data = {
            "question_id": result.question.id,
            "content": result.content,
            "category": result.category,
            "difficulty": result.difficulty,
            "correct_answer": result.correct_answer,
            "incorrect_answers": result.incorrect_answers,
            "user_id": result.user_id
        }
        
        print(f"\nComplete data: {json.dumps(display_data, indent=2)}")
        return result
    except Exception as e:
        print(f"Error uploading question: {e}")
        return None

async def create_system_user():
    """Create the system user directly"""
    client = await setup_supabase()
    actions = SupabaseActions(client)
    
    print("\nCreating system user (00000000-0000-0000-0000-000000000000)...")
    
    try:
        user_data = await actions.ensure_user_exists(
            "00000000-0000-0000-0000-000000000000", 
            "system"
        )
        print("System user created or verified successfully!")
        print(f"User data: {json.dumps(user_data, indent=2)}")
        return True
    except Exception as e:
        print(f"Error creating system user: {e}")
        return False

async def test_guidelines_generation():
    """Test generation of category guidelines and difficulty tiers"""
    # Create LLM config
    llm_config = LLMConfigFactory.create_default()
    
    # Initialize helpers
    category_helper = CategoryHelper(llm_config)
    difficulty_helper = DifficultyHelper(llm_config)
    
    # Get category input
    category = input("Enter category to generate guidelines for: ")
    if not category:
        category = "General Knowledge"
    
    # Get category guidelines
    print(f"\n--- CATEGORY GUIDELINES FOR '{category}' ---")
    category_guidelines = category_helper.generate_category_guidelines(category)
    
    # Generate difficulty tiers
    print(f"\n--- DIFFICULTY TIERS FOR '{category}' ---")
    difficulty_tiers = difficulty_helper.generate_difficulty_guidelines(category)
    
    # Display each difficulty tier
    for level in ["Easy", "Medium", "Hard", "Expert", "Master"]:
        if level in difficulty_tiers:
            print(f"\n{level}:")
            print(difficulty_tiers[level])

async def test_concurrent_guideline_generation():
    """Test concurrent generation of guidelines using asyncio"""
    # Create LLM config
    llm_config = LLMConfigFactory.create_default()
    
    # Initialize helpers
    category_helper = CategoryHelper(llm_config)
    difficulty_helper = DifficultyHelper(llm_config)
    
    # Get category input
    category = input("Enter category to generate guidelines for: ")
    if not category:
        category = "General Knowledge"
    
    print(f"\nGenerating guidelines concurrently for '{category}'...")
    
    # Timing the operation
    start_time = time.time()
    
    # Create tasks for concurrent execution
    category_task = asyncio.create_task(
        asyncio.to_thread(category_helper.generate_category_guidelines, category)
    )
    
    difficulty_task = asyncio.create_task(
        asyncio.to_thread(difficulty_helper.generate_difficulty_guidelines, category)
    )
    
    # Wait for both to complete concurrently
    category_guidelines, difficulty_tiers = await asyncio.gather(
        category_task, 
        difficulty_task
    )
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    print(f"\nGuidelines generated concurrently in {elapsed_time:.2f} seconds")
    
    # Display category guidelines
    print(f"\n--- CATEGORY GUIDELINES FOR '{category}' ---")
    print(category_guidelines)
    
    # Display each difficulty tier
    print(f"\n--- DIFFICULTY TIERS FOR '{category}' ---")
    for level in ["Easy", "Medium", "Hard", "Expert", "Master"]:
        if level in difficulty_tiers:
            print(f"\n{level}:")
            print(difficulty_tiers[level])

async def test_multi_difficulty_generation():
    """Test generating questions with multiple difficulty levels concurrently"""
    question_service, _ = await setup_question_service()
    
    # Get test parameters
    print("\nMULTI-DIFFICULTY QUESTION GENERATION")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
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
    print(f"\nGenerating {total_count} '{category}' questions across {len(difficulty_counts)} difficulty levels...")
    print(f"Difficulty distribution: {difficulty_counts}")
    
    # Timing starts before any operations begin
    start_time = time.time()
    
    try:
        result = await question_service.create_multi_difficulty_question_set(
            category=category,
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
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main interactive test function"""
    print("=" * 50)
    print("MANUAL TEST FOR TRIVIA APP (ENHANCED)".center(50))
    print("=" * 50)
    print("\nWhat would you like to test?")
    print("1. Create a new user")
    print("2. Upload a question (as system user)")
    print("3. Create a user and upload a question as that user")
    print("4. Create system user (00000000-0000-0000-0000-000000000000)")
    print("5. Generate questions with a specific difficulty")
    print("6. Generate complete questions with answers")
    print("7. Generate category guidelines and difficulty tiers")
    print("8. Generate questions using ASYNC method (concurrent)")
    print("9. Generate complete questions using ASYNC methods (concurrent)")
    print("10. Generate guidelines concurrently")
    print("11. Generate questions with multiple difficulties concurrently")
    print("12. Exit")
    
    choice = input("\nEnter your choice (1-12): ")
    
    if choice == "1":
        await test_user_creation()
    elif choice == "2":
        await test_question_upload()
    elif choice == "3":
        user_id = await test_user_creation()
        if user_id:
            await test_question_upload(user_id)
    elif choice == "4":
        await create_system_user()
    elif choice == "5":
        await test_single_difficulty_generation()
    elif choice == "6":
        await test_complete_question_generation()
    elif choice == "7": 
        await test_guidelines_generation()
    elif choice == "8":
        await test_async_question_generation()
    elif choice == "9":
        await test_async_complete_generation()
    elif choice == "10":
        await test_concurrent_guideline_generation()
    elif choice == "11":
        await test_multi_difficulty_generation()
    elif choice == "12":
        print("Exiting...")
        return
    else:
        print("Invalid choice. Please try again.")
    
    # Ask if the user wants to continue
    continue_testing = input("\nWould you like to continue testing? (y/n): ")
    if continue_testing.lower() == "y":
        await main()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)