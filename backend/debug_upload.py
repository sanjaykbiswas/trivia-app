#!/usr/bin/env python3
"""
Debug Upload API
Direct test of upload functionality to isolate API issues
"""

import sys
import os
import traceback
import asyncio
import uuid
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

async def test_upload_service():
    """Test the UploadService directly (bypassing the API)"""
    print("\n===== TESTING UPLOAD SERVICE DIRECTLY =====")
    
    try:
        # Import required modules
        import supabase
        from config.environment import Environment
        from services.upload_service import UploadService
        
        # Load environment variables
        load_dotenv()
        
        # Initialize the environment
        env = Environment()
        supabase_url = env.get("supabase_url")
        supabase_key = env.get("supabase_key")
        
        print(f"Using Supabase URL: {supabase_url}")
        print(f"API key available: {'Yes' if supabase_key else 'No'}")
        
        # Create Supabase client
        client = supabase.create_client(supabase_url, supabase_key)
        
        # Create upload service
        upload_service = UploadService(client)
        
        # Use system user ID
        system_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Test upload_complete_question method
        print("\nTesting upload_complete_question method...")
        
        test_data = {
            "question_content": "What is the capital of France?",
            "category": "Geography",
            "correct_answer": "Paris",
            "incorrect_answers": ["London", "Berlin", "Rome"],
            "difficulty": "Easy",
            "user_id": system_user_id
        }
        
        print(f"Uploading test data: {test_data}")
        
        result = await upload_service.upload_complete_question(**test_data)
        
        print("\nUpload result:")
        print(f"- Question ID: {result.question.id}")
        print(f"- Question content: {result.question.content}")
        print(f"- Answer ID: {result.answer.id}")
        print(f"- Correct answer: {result.answer.correct_answer}")
        
        print("\n✅ UploadService test successful!")
        return result
    except Exception as e:
        print(f"\n❌ Error testing UploadService: {str(e)}")
        traceback.print_exc()
        return None

async def test_upload_controller():
    """Test the UploadController directly (simulating API calls)"""
    print("\n===== TESTING UPLOAD CONTROLLER DIRECTLY =====")
    
    try:
        # Import required modules
        import supabase
        from config.environment import Environment
        from services.upload_service import UploadService
        from controllers.upload_controller import UploadController, QuestionUploadRequest
        
        # Load environment variables
        load_dotenv()
        
        # Initialize the environment
        env = Environment()
        supabase_url = env.get("supabase_url")
        supabase_key = env.get("supabase_key")
        
        # Create Supabase client
        client = supabase.create_client(supabase_url, supabase_key)
        
        # Create upload service
        upload_service = UploadService(client)
        
        # Create upload controller with the service
        upload_controller = UploadController(upload_service)
        
        # Create a request object
        request = QuestionUploadRequest(
            content="What is the largest planet in our solar system?",
            category="Science",
            correct_answer="Jupiter",
            incorrect_answers=["Saturn", "Neptune", "Uranus"],
            difficulty="Medium",
            user_id="00000000-0000-0000-0000-000000000000"
        )
        
        print(f"Created request object: {request}")
        
        # Call the controller method directly
        print("\nCalling upload_question method on controller...")
        result = await upload_controller.upload_question(request)
        
        print("\nController result:")
        print(f"- ID: {result.id}")
        print(f"- Content: {result.content}")
        print(f"- Category: {result.category}")
        print(f"- Correct answer: {result.correct_answer}")
        
        print("\n✅ UploadController test successful!")
        return result
    except Exception as e:
        print(f"\n❌ Error testing UploadController: {str(e)}")
        traceback.print_exc()
        return None

async def test_api_directly():
    """Test the API endpoint directly"""
    print("\n===== TESTING API ENDPOINT DIRECTLY =====")
    
    try:
        # Create a test client for FastAPI
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # Prepare test data
        test_data = {
            "content": "Who wrote Romeo and Juliet?",
            "category": "Literature",
            "correct_answer": "William Shakespeare",
            "incorrect_answers": ["Charles Dickens", "Jane Austen", "Mark Twain"],
            "difficulty": "Easy",
            "user_id": "00000000-0000-0000-0000-000000000000"
        }
        
        print(f"Test data: {test_data}")
        
        # Make request to upload endpoint
        print("\nMaking request to /upload/question...")
        response = client.post("/upload/question", json=test_data)
        
        print(f"Status code: {response.status_code}")
        
        # Try to parse response
        try:
            result = response.json()
            print(f"Response JSON: {result}")
            
            if response.status_code == 200:
                print("\n✅ API endpoint test successful!")
            else:
                print("\n❌ API endpoint test failed with non-200 status code")
                
            return result
        except Exception as e:
            print(f"Error parsing response as JSON: {str(e)}")
            print(f"Raw response text: {response.text[:500]}")
            
            # Look for traceback in response
            if "Traceback" in response.text:
                tb_start = response.text.find("Traceback")
                tb_end = response.text.find("</pre>", tb_start) if "</pre>" in response.text else len(response.text)
                print("\nError traceback from response:")
                print(response.text[tb_start:tb_end])
            
            return None
    except Exception as e:
        print(f"\n❌ Error testing API endpoint directly: {str(e)}")
        traceback.print_exc()
        return None

async def fix_upload_controller():
    """Attempt to identify and fix issues in the UploadController"""
    print("\n===== FIXING UPLOAD CONTROLLER =====")
    
    try:
        import inspect
        from controllers.upload_controller import UploadController
        
        # Get controller class source code
        source = inspect.getsource(UploadController)
        print(f"Controller source code length: {len(source)} characters")
        
        # Check for async methods
        print("\nChecking for async methods...")
        methods = inspect.getmembers(UploadController, predicate=inspect.isfunction)
        
        for name, method in methods:
            if name.startswith('_'):
                continue
            
            is_async = inspect.iscoroutinefunction(method)
            print(f"Method '{name}': {'async' if is_async else 'sync'}")
            
            # Check if route handler methods are async
            if name in ['upload_question', 'bulk_upload_questions', 'register_user']:
                if not is_async:
                    print(f"⚠️ Warning: '{name}' should be async for FastAPI to work correctly")
                    
                    # Check if method calls any async functions
                    source = inspect.getsource(method)
                    if 'await' in source:
                        print(f"  ❌ Method '{name}' contains 'await' but is not defined as async")
                    else:
                        print(f"  ℹ️ Method '{name}' doesn't contain 'await', might not need to be async")
        
        print("\nChecking for common issues...")
        
        # Check service injection
        from controllers.upload_controller import UploadController
        init_src = inspect.getsource(UploadController.__init__)
        
        if 'self.upload_service = upload_service' in init_src:
            print("✅ Service is properly stored in controller")
        else:
            print("❌ Service might not be properly stored in controller constructor")
        
        # Check router setup
        if '_setup_routes' in [name for name, _ in methods]:
            print("✅ Found _setup_routes method")
        else:
            print("❌ Missing _setup_routes method")
        
        print("\nFix analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error analyzing UploadController: {str(e)}")
        traceback.print_exc()

async def main():
    """Main function for testing and debugging"""
    print("=" * 70)
    print("DEBUG UPLOAD API".center(70))
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    # Step 1: Test the upload service directly
    service_result = await test_upload_service()
    
    if service_result:
        # Step 2: Test the controller directly
        controller_result = await test_upload_controller()
        
        if controller_result:
            # Step 3: Test the API directly
            api_result = await test_api_directly()
            
            if not api_result:
                # Step 4: Try to identify and fix issues
                await fix_upload_controller()
        else:
            print("\nSkipping API test since controller test failed")
            await fix_upload_controller()
    else:
        print("\nSkipping controller and API tests since service test failed")
    
    print("\nDebug process complete!")

if __name__ == "__main__":
    asyncio.run(main())