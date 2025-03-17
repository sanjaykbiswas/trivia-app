import pytest
import asyncio
import uuid
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config.environment import Environment
from utils.supabase_actions import SupabaseActions
from services.upload_service import UploadService
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("upload_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("upload_tests")

# Initialize environment and Supabase client
async def setup_supabase():
    """Create Supabase client for testing"""
    import supabase
    env = Environment()
    client = supabase.create_client(
        supabase_url=env.get("supabase_url"),
        supabase_key=env.get("supabase_key")
    )
    return client

# Test cases
async def test_user_creation():
    """Test user creation functionality"""
    logger.info("STARTING TEST: User Creation")
    
    # Create a unique user ID for this test
    test_user_id = str(uuid.uuid4())
    test_username = f"test_user_{test_user_id[:8]}"
    
    client = await setup_supabase()
    actions = SupabaseActions(client)
    
    try:
        # Test creating a new user
        logger.info(f"Creating test user: {test_user_id}")
        user_data = await actions.ensure_user_exists(test_user_id, test_username)
        
        assert user_data is not None, "User data should not be None"
        assert user_data["id"] == test_user_id, "User ID should match"
        assert user_data["username"] == test_username, "Username should match"
        
        # Test retrieving the same user (should not create a new one)
        logger.info(f"Retrieving existing user: {test_user_id}")
        existing_user = await actions.ensure_user_exists(test_user_id)
        
        assert existing_user is not None, "User data should not be None"
        assert existing_user["id"] == test_user_id, "User ID should match"
        
        logger.info("User creation test PASSED")
        return True
    except Exception as e:
        logger.error(f"User creation test FAILED: {str(e)}")
        return False

async def test_question_upload():
    """Test question upload functionality"""
    logger.info("STARTING TEST: Question Upload")
    
    # Create test data
    test_user_id = str(uuid.uuid4())
    test_question = Question(
        content="What is the capital of France?",
        category="Geography",
        difficulty="Easy",
        user_id=test_user_id
    )
    test_answer = Answer(
        question_id="",  # Will be filled by the service
        correct_answer="Paris",
        incorrect_answers=["London", "Berlin", "Madrid"]
    )
    
    client = await setup_supabase()
    actions = SupabaseActions(client)
    
    try:
        # Test saving a question and answer
        logger.info("Saving test question and answer")
        result = await actions.save_question_and_answer(test_question, test_answer)
        
        assert "question" in result, "Result should contain question data"
        assert "answer" in result, "Result should contain answer data"
        
        saved_question = result["question"]
        saved_answer = result["answer"]
        
        assert saved_question.id is not None, "Question should have an ID"
        assert saved_answer.id is not None, "Answer should have an ID"
        assert saved_answer.question_id == saved_question.id, "Answer should reference question ID"
        
        logger.info("Question upload test PASSED")
        return True
    except Exception as e:
        logger.error(f"Question upload test FAILED: {str(e)}")
        return False

async def test_upload_service():
    """Test the upload service functionality"""
    logger.info("STARTING TEST: Upload Service")
    
    client = await setup_supabase()
    upload_service = UploadService(client)
    
    test_user_id = str(uuid.uuid4())
    
    try:
        # Test uploading a complete question
        logger.info("Testing upload_complete_question method")
        result = await upload_service.upload_complete_question(
            question_content="What is the largest planet in our solar system?",
            category="Science",
            correct_answer="Jupiter",
            incorrect_answers=["Saturn", "Neptune", "Uranus"],
            difficulty="Medium",
            user_id=test_user_id
        )
        
        assert isinstance(result, CompleteQuestion), "Result should be a CompleteQuestion object"
        assert result.question.id is not None, "Question should have an ID"
        assert result.answer.id is not None, "Answer should have an ID"
        assert result.content == "What is the largest planet in our solar system?", "Question content should match"
        assert result.correct_answer == "Jupiter", "Correct answer should match"
        
        # Test bulk upload
        logger.info("Testing bulk_upload_complete_questions method")
        bulk_data = [
            {
                "content": "What is the smallest prime number?",
                "category": "Mathematics",
                "correct_answer": "2",
                "incorrect_answers": ["1", "0", "3"],
                "difficulty": "Easy",
                "user_id": test_user_id
            },
            {
                "content": "Who painted the Mona Lisa?",
                "category": "Art",
                "correct_answer": "Leonardo da Vinci",
                "incorrect_answers": ["Michelangelo", "Rafael", "Vincent van Gogh"],
                "difficulty": "Easy",
                "user_id": test_user_id
            }
        ]
        
        bulk_results = await upload_service.bulk_upload_complete_questions(bulk_data)
        
        assert len(bulk_results) == 2, "Should return 2 results"
        assert all(isinstance(item, CompleteQuestion) for item in bulk_results), "All results should be CompleteQuestion objects"
        
        logger.info("Upload service test PASSED")
        return True
    except Exception as e:
        logger.error(f"Upload service test FAILED: {str(e)}")
        return False

# Main test runner
async def run_tests():
    """Run all tests"""
    logger.info("=== STARTING UPLOAD FUNCTIONALITY TESTS ===")
    
    test_results = {
        "user_creation": await test_user_creation(),
        "question_upload": await test_question_upload(),
        "upload_service": await test_upload_service()
    }
    
    # Summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    for test_name, passed in test_results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    if all(test_results.values()):
        logger.info("All tests PASSED!")
        return True
    else:
        logger.warning("Some tests FAILED!")
        return False

# Run the tests when the script is executed directly
if __name__ == "__main__":
    asyncio.run(run_tests())