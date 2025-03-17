#!/usr/bin/env python3
"""
Test runner script for trivia app
Run all tests and display results
"""

import asyncio
import argparse
import sys
import time
import os
import logging
import importlib.util

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Check for required dependencies
required_packages = ['pytest', 'fastapi', 'httpx']
missing_packages = []

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        missing_packages.append(package)

if missing_packages:
    print("Missing required packages. Please install them with pip:")
    print(f"pip install {' '.join(missing_packages)}")
    sys.exit(1)

# Import logging configuration
try:
    from utils.logging_config import setup_logging
except ImportError:
    print("ERROR: Cannot import utils.logging_config.")
    print("Make sure the logging_config.py file is in the correct location.")
    print("Expected path: utils/logging_config.py")
    sys.exit(1)

def banner(text, width=70):
    """Print a banner with text centered"""
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

async def run_upload_tests():
    """Run upload functionality tests"""
    try:
        from tests.test_upload import run_tests as run_upload_tests
        
        banner("UPLOAD FUNCTIONALITY TESTS")
        return await run_upload_tests()
    except ImportError as e:
        print(f"ERROR: Could not import upload tests: {e}")
        print("Make sure the test_upload.py file is in the tests directory.")
        return False

def run_api_tests():
    """Run API endpoint tests"""
    try:
        from tests.test_api import run_tests as run_api_tests
        
        banner("API ENDPOINT TESTS")
        return run_api_tests()
    except ImportError as e:
        print(f"ERROR: Could not import API tests: {e}")
        print("Make sure the test_api.py file is in the tests directory.")
        return False

async def main():
    """Main test runner function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Trivia App Tests")
    parser.add_argument("--upload", action="store_true", help="Run upload functionality tests only")
    parser.add_argument("--api", action="store_true", help="Run API endpoint tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(app_name="test_runner", log_level=logging.INFO)
    
    # Determine which tests to run
    run_all = args.all or (not args.upload and not args.api)
    
    start_time = time.time()
    results = {}
    
    # Run selected tests
    try:
        if args.upload or run_all:
            results["upload"] = await run_upload_tests()
        
        if args.api or run_all:
            results["api"] = run_api_tests()
    
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return False
    
    # Display summary
    elapsed_time = time.time() - start_time
    
    banner("TEST RESULTS SUMMARY")
    for test_type, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{test_type.upper()} Tests: {status}")
    
    print(f"\nTotal time: {elapsed_time:.2f} seconds")
    
    # Return overall success/failure
    return all(results.values())

if __name__ == "__main__":
    # Ensure proper directory structure for tests
    os.makedirs("tests", exist_ok=True)
    
    # Create __init__.py in tests directory if it doesn't exist
    init_file = os.path.join("tests", "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("# Test package\n")
    
    # Move test files to tests directory if they're not there
    for test_file in ["test_upload.py", "test_api.py"]:
        source_path = test_file
        target_path = os.path.join("tests", test_file)
        
        if os.path.exists(source_path) and not os.path.exists(target_path):
            print(f"Moving {source_path} to {target_path}")
            os.rename(source_path, target_path)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the tests
    success = asyncio.run(main())
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)