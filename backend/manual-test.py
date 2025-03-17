#!/usr/bin/env python3
"""
Manual test script for upload functionality
This script allows you to manually test the upload functionality
"""

import asyncio
import uuid
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List
from config.environment import Environment
from utils.supabase_actions import SupabaseActions
from services.upload_service import UploadService
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

async def test_user_creation():
    """Test creating a new user"""
    client = await setup_supabase()
    actions = SupabaseActions(client)
    
    # Generate a unique ID
    user_id = str(uuid.uuid4())
    
    # Get username from user
    username = input("Enter a username (or press Enter to use a generated one): ")
    if not username:
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

async def main():
    """Main interactive test function"""
    print("=" * 50)
    print("MANUAL TEST FOR UPLOAD FUNCTIONALITY".center(50))
    print("=" * 50)
    print("\nWhat would you like to test?")
    print("1. Create a new user")
    print("2. Upload a question (as system user)")
    print("3. Create a user and upload a question as that user")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        await test_user_creation()
    elif choice == "2":
        await test_question_upload()
    elif choice == "3":
        user_id = await test_user_creation()
        if user_id:
            await test_question_upload(user_id)
    elif choice == "4":
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