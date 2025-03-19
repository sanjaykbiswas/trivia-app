#!/usr/bin/env python3
"""
Manual test script for trivia app functionality
This script allows you to manually test various functionalities
"""

import asyncio
import uuid
import json
import sys
import os
import logging
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

# Setup logging
logger = setup_logging(app_name="manual_test", log_level=logging.INFO)

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
    
    count = input("Number of questions to generate (1-10): ")
    try:
        count = int(count)
        if count < 1 or count > 10:
            count = 3
    except ValueError:
        count = 3
    
    print(f"\nGenerating {count} '{category}' questions with '{difficulty}' difficulty...")
    
    try:
        questions = await question_service.generate_and_save_questions(
            category=category,
            count=count,
            deduplicate=True,
            difficulty=difficulty
        )
        
        print(f"Successfully generated {len(questions)} questions")
        
        # Display questions
        for i, question in enumerate(questions):
            print(f"\nQuestion {i+1}: {question.content}")
            print(f"Difficulty: {question.difficulty}")
            print(f"ID: {question.id}")
        
        return True
    except Exception as e:
        print(f"Error during question generation: {e}")
        return False

async def test_multi_difficulty_generation():
    """Test generating questions with multiple difficulty levels"""
    question_service, _ = await setup_question_service()
    
    # Get test parameters
    print("\nMULTI-DIFFICULTY QUESTION GENERATION")
    print("=" * 40)
    
    category = input("Enter category (e.g., History, Science, Movies): ")
    if not category:
        category = "General Knowledge"
    
    # Get difficulties
    print("\nSelect difficulties (enter 'y' for each one you want):")
    difficulties = []
    
    for diff in ["Easy", "Medium", "Hard", "Expert", "Master"]:
        include = input(f"Include {diff}? (y/n): ")
        if include.lower() == 'y':
            difficulties.append(diff)
    
    # Default to Medium if none selected
    if not difficulties:
        print("No difficulties selected. Using Medium as default.")
        difficulties = ["Medium"]
    
    count = input("Total number of questions to generate (2-10): ")
    try:
        count = int(count)
        if count < 2 or count > 10:
            count = 6
    except ValueError:
        count = 6
    
    print(f"\nGenerating {count} '{category}' questions across {len(difficulties)} difficulties...")
    print(f"Selected difficulties: {', '.join(difficulties)}")
    
    try:
        complete_questions = await question_service.create_complete_question_set(
            category=category,
            count=count,
            deduplicate=True,
            difficulties=difficulties
        )
        
        print(f"Successfully generated {len(complete_questions)} complete questions with answers")
        
        # Count by difficulty
        difficulty_counts = {}
        for q in complete_questions:
            difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1
        
        print(f"\nQuestions by difficulty: {difficulty_counts}")
        
        # Display questions
        for i, question in enumerate(complete_questions):
            print(f"\nQuestion {i+1}: {question.content}")
            print(f"Difficulty: {question.difficulty}")
            print(f"Correct answer: {question.correct_answer}")
            print(f"Incorrect answers: {question.incorrect_answers}")
        
        return True
    except Exception as e:
        print(f"Error during multi-difficulty question generation: {e}")
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

async def main():
    """Main interactive test function"""
    print("=" * 50)
    print("MANUAL TEST FOR TRIVIA APP".center(50))
    print("=" * 50)
    print("\nWhat would you like to test?")
    print("1. Create a new user")
    print("2. Upload a question (as system user)")
    print("3. Create a user and upload a question as that user")
    print("4. Create system user (00000000-0000-0000-0000-000000000000)")
    print("5. Generate questions with a single difficulty")
    print("6. Generate questions with multiple difficulties")
    print("7. Exit")
    
    choice = input("\nEnter your choice (1-7): ")
    
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
        await test_multi_difficulty_generation()
    elif choice == "7":
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