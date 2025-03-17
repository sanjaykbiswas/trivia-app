import pytest
import uuid
import logging
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from fastapi.testclient import TestClient
try:
    from main import app
except ImportError:
    try:
        # Try alternate import path
        from src.main import app
    except ImportError:
        # If both fail, raise an error
        raise ImportError("Could not import 'app' from main.py - make sure the file exists and the path is correct")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("api_tests")

# Create test client
client = TestClient(app)

def test_upload_question_endpoint():
    """Test the /upload/question endpoint"""
    logger.info("TESTING ENDPOINT: POST /upload/question")
    
    # Create test data
    test_user_id = str(uuid.uuid4())
    test_data = {
        "content": "What is the capital of France?",
        "category": "Geography",
        "correct_answer": "Paris",
        "incorrect_answers": ["London", "Berlin", "Madrid"],
        "difficulty": "Easy",
        "user_id": test_user_id
    }
    
    # Send request
    response = client.post("/upload/question", json=test_data)
    
    # Check response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert "id" in data, "Response should include question ID"
    assert data["content"] == test_data["content"], "Question content should match"
    assert data["correct_answer"] == test_data["correct_answer"], "Correct answer should match"
    
    logger.info(f"Created question with ID: {data['id']}")
    logger.info("Test PASSED")
    
    return data["id"]  # Return ID for use in other tests

def test_bulk_upload_endpoint():
    """Test the /upload/questions/bulk endpoint"""
    logger.info("TESTING ENDPOINT: POST /upload/questions/bulk")
    
    # Create test data
    test_user_id = str(uuid.uuid4())
    test_data = {
        "questions": [
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
    }
    
    # Send request
    response = client.post("/upload/questions/bulk", json=test_data)
    
    # Check response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, "Response should contain 2 items"
    
    for idx, item in enumerate(data):
        assert "id" in item, "Each item should have an ID"
        assert item["content"] == test_data["questions"][idx]["content"], "Question content should match"
    
    logger.info(f"Created {len(data)} questions in bulk")
    logger.info("Test PASSED")
    
    return [item["id"] for item in data]  # Return IDs for use in other tests

def test_register_user_endpoint():
    """Test the /upload/user endpoint"""
    logger.info("TESTING ENDPOINT: POST /upload/user")
    
    # Create test data
    test_user_id = str(uuid.uuid4())
    test_username = f"test_user_{test_user_id[:8]}"
    
    test_data = {
        "user_id": test_user_id,
        "username": test_username
    }
    
    # Send request
    response = client.post("/upload/user", json=test_data)
    
    # Check response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert "id" in data, "Response should include user ID"
    assert data["id"] == test_user_id, "User ID should match"
    assert data["username"] == test_username, "Username should match"
    
    logger.info(f"Registered user with ID: {data['id']}")
    logger.info("Test PASSED")
    
    return data["id"]  # Return ID for use in other tests

def test_get_question_endpoint(question_id):
    """Test the /questions/{question_id} endpoint"""
    logger.info(f"TESTING ENDPOINT: GET /questions/{question_id}")
    
    # Send request
    response = client.get(f"/questions/{question_id}")
    
    # Check response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert "id" in data, "Response should include question ID"
    assert data["id"] == question_id, "Question ID should match"
    
    logger.info("Test PASSED")

def run_tests():
    """Run all API tests"""
    logger.info("=== STARTING API ENDPOINT TESTS ===")
    
    # Run tests
    try:
        question_id = test_upload_question_endpoint()
        bulk_ids = test_bulk_upload_endpoint()
        user_id = test_register_user_endpoint()
        
        # Test retrieval of uploaded question
        test_get_question_endpoint(question_id)
        
        logger.info("=== ALL API TESTS PASSED ===")
        return True
    except Exception as e:
        logger.error(f"API TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    run_tests()