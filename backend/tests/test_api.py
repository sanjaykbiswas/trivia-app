import requests
import json
import sys
import time
import argparse
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid
import os # Added os
from pathlib import Path # Added Path

# --- ADD THIS BLOCK ---
# Add the project root (backend/) to the Python path
# This allows importing 'src' even when running this script directly from tests/
script_path = Path(__file__).resolve() # Gets the path of the current script
project_root = script_path.parent.parent # Go up two levels (tests/ -> backend/)
sys.path.insert(0, str(project_root))
# --- END ADDED BLOCK ---

# Imports from src should now work
# e.g., if you needed to import something from src: from src.models import Pack

# API base URL
BASE_URL = "http://localhost:8000/api"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Test case result type
class ResultType(Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    SKIP = "SKIP"

class APITester:
    def __init__(self, base_url: str = BASE_URL, verbose: bool = False):
        """Initialize the API tester."""
        self.base_url = base_url
        self.verbose = verbose
        self.pack_id = None
        self.results = []

    def log(self, message: str, end="\n") -> None:
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(message, end=end)

    def print_json(self, data: Any) -> None:
        """Pretty print JSON data."""
        if self.verbose:
            print(json.dumps(data, indent=2))

    def record_result(self, test_name: str, result_type: ResultType, message: str = "", data: Any = None) -> None:
        """Record the test result."""
        self.results.append({
            "test_name": test_name,
            "result_type": result_type,
            "message": message,
            "data": data
        })

        # Print result to console
        color = Colors.GREEN if result_type == ResultType.SUCCESS else \
                Colors.WARNING if result_type == ResultType.SKIP else Colors.FAIL

        result_str = f"{color}{result_type.value}{Colors.ENDC}"
        message_str = f" - {message}" if message else ""

        print(f"{test_name}: {result_str}{message_str}")

        if data and self.verbose:
            self.print_json(data)

    def run_test(self, test_func, test_name: str, skip_condition: bool = False) -> Any:
        """Run a test function and record the result."""
        if skip_condition:
            self.record_result(test_name, ResultType.SKIP, "Test skipped due to dependency failure")
            return None

        try:
            print(f"{Colors.BOLD}Running test: {test_name}{Colors.ENDC}")
            result = test_func()
            return result
        except Exception as e:
            self.record_result(test_name, ResultType.FAIL, f"Exception: {str(e)}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return None

    def test_pack_creation(self) -> str:
        """Test creating a new pack."""
        test_name = "Create Pack"

        # Generate a unique pack name to avoid conflicts
        pack_name = f"Test Pack {uuid.uuid4().hex[:8]}"

        data = {
            "name": pack_name,
            "description": "A test pack for API testing",
            "price": 0.0,
            "creator_type": "system"
        }

        self.log(f"Creating pack with name: {pack_name}")
        response = requests.post(f"{self.base_url}/packs/", json=data)

        if response.status_code == 201:
            response_data = response.json()
            pack_id = response_data.get("id")
            self.pack_id = pack_id
            self.record_result(test_name, ResultType.SUCCESS, f"Created pack: {pack_name}", response_data)
            return pack_id
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_generate_topics(self) -> List[str]:
        """Test generating topics for a pack."""
        test_name = "Generate Topics"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        # --- MODIFIED: Removed creation_name ---
        data = {
            "num_topics": 5
            # "creation_name": "Test Pack" # Removed
        }
        # --- END MODIFIED ---

        self.log(f"Generating topics for pack ID: {self.pack_id}")
        response = requests.post(f"{self.base_url}/packs/{self.pack_id}/topics/", json=data)

        if response.status_code == 200:
            response_data = response.json()
            topics = response_data.get("topics", [])
            self.record_result(test_name, ResultType.SUCCESS, f"Generated {len(topics)} topics", response_data)
            return topics
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_get_topics(self) -> List[str]:
        """Test retrieving topics for a pack."""
        test_name = "Get Topics"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        self.log(f"Getting topics for pack ID: {self.pack_id}")
        response = requests.get(f"{self.base_url}/packs/{self.pack_id}/topics/")

        if response.status_code == 200:
            response_data = response.json()
            topics = response_data.get("topics", [])
            self.record_result(test_name, ResultType.SUCCESS, f"Retrieved {len(topics)} topics", response_data)
            return topics
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_generate_difficulties(self) -> Dict[str, Any]:
        """Test generating difficulty descriptions for a pack."""
        test_name = "Generate Difficulties"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        # --- MODIFIED: Removed creation_name ---
        data = {
            # "creation_name": "Test Pack", # Removed
            "force_regenerate": True
        }
        # --- END MODIFIED ---

        self.log(f"Generating difficulty descriptions for pack ID: {self.pack_id}")
        response = requests.post(f"{self.base_url}/packs/{self.pack_id}/difficulties/", json=data)

        if response.status_code == 200:
            response_data = response.json()
            descriptions = response_data.get("descriptions", {})
            self.record_result(test_name, ResultType.SUCCESS, f"Generated difficulty descriptions", response_data)
            return descriptions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_get_difficulties(self) -> Dict[str, Any]:
        """Test retrieving difficulty descriptions for a pack."""
        test_name = "Get Difficulties"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        self.log(f"Getting difficulty descriptions for pack ID: {self.pack_id}")
        response = requests.get(f"{self.base_url}/packs/{self.pack_id}/difficulties/")

        if response.status_code == 200:
            response_data = response.json()
            descriptions = response_data.get("descriptions", {})
            self.record_result(test_name, ResultType.SUCCESS, f"Retrieved difficulty descriptions", response_data)
            return descriptions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_store_seed_questions(self) -> Dict[str, str]:
        """Test storing seed questions for a pack."""
        test_name = "Store Seed Questions"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        data = {
            "seed_questions": {
                "What is the capital of France?": "Paris",
                "Who wrote 'Romeo and Juliet'?": "William Shakespeare",
                "What is the chemical symbol for gold?": "Au"
            }
        }

        self.log(f"Storing seed questions for pack ID: {self.pack_id}")
        response = requests.post(f"{self.base_url}/packs/{self.pack_id}/questions/seed", json=data)

        if response.status_code == 200:
            response_data = response.json()
            seed_questions = response_data.get("seed_questions", {})
            self.record_result(test_name, ResultType.SUCCESS, f"Stored {len(seed_questions)} seed questions", response_data)
            return seed_questions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_extract_seed_questions(self) -> Dict[str, str]:
        """Test extracting seed questions from text."""
        test_name = "Extract Seed Questions"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        data = {
            "text_content": """
            Q: What is the largest planet in our solar system?
            A: Jupiter

            Question: How many continents are there on Earth?
            Answer: Seven

            Q: Who painted the Mona Lisa?
            A: Leonardo da Vinci
            """
        }

        self.log(f"Extracting seed questions for pack ID: {self.pack_id}")
        response = requests.post(f"{self.base_url}/packs/{self.pack_id}/questions/seed/extract", json=data)

        if response.status_code == 200:
            response_data = response.json()
            seed_questions = response_data.get("seed_questions", {})
            self.record_result(test_name, ResultType.SUCCESS, f"Extracted {len(seed_questions)} seed questions", response_data)
            return seed_questions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_get_seed_questions(self) -> Dict[str, str]:
        """Test retrieving seed questions for a pack."""
        test_name = "Get Seed Questions"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        self.log(f"Getting seed questions for pack ID: {self.pack_id}")
        response = requests.get(f"{self.base_url}/packs/{self.pack_id}/questions/seed")

        if response.status_code == 200:
            response_data = response.json()
            seed_questions = response_data.get("seed_questions", {})
            self.record_result(test_name, ResultType.SUCCESS, f"Retrieved {len(seed_questions)} seed questions", response_data)
            return seed_questions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_generate_questions(self, topic: str = None) -> List[Dict[str, Any]]:
        """Test generating questions for a pack."""
        test_name = "Generate Questions"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        # Get topics if not provided
        if not topic:
            topics = self.test_get_topics()
            if topics and len(topics) > 0:
                topic = topics[0]
            else:
                self.record_result(test_name, ResultType.SKIP, "No topics available")
                return None

        data = {
            "pack_topic": topic,
            "difficulty": "medium",
            "num_questions": 3,
            "debug_mode": self.verbose
        }

        self.log(f"Generating questions for pack ID: {self.pack_id}, topic: {topic}")
        response = requests.post(f"{self.base_url}/packs/{self.pack_id}/questions/", json=data)

        if response.status_code == 200:
            response_data = response.json()
            questions = response_data.get("questions", [])
            self.record_result(test_name, ResultType.SUCCESS, f"Generated {len(questions)} questions", response_data)
            return questions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def test_get_questions(self) -> List[Dict[str, Any]]:
        """Test retrieving questions for a pack."""
        test_name = "Get Questions"

        if not self.pack_id:
            self.record_result(test_name, ResultType.SKIP, "No pack ID available")
            return None

        self.log(f"Getting questions for pack ID: {self.pack_id}")
        response = requests.get(f"{self.base_url}/packs/{self.pack_id}/questions/")

        if response.status_code == 200:
            response_data = response.json()
            questions = response_data.get("questions", [])
            self.record_result(test_name, ResultType.SUCCESS, f"Retrieved {len(questions)} questions", response_data)
            return questions
        else:
            self.record_result(test_name, ResultType.FAIL, f"Failed with status code: {response.status_code}", response.json())
            return None

    def run_all_tests(self) -> None:
        """Run all API tests in sequence."""
        print(f"{Colors.HEADER}Starting API Tests{Colors.ENDC}")
        print(f"Base URL: {self.base_url}")

        # Test creating a pack
        pack_id = self.run_test(self.test_pack_creation, "Create Pack")

        # Don't continue if pack creation failed
        if not pack_id:
            print(f"{Colors.FAIL}Pack creation failed. Stopping tests.{Colors.ENDC}")
            return

        # Test generating topics
        topics = self.run_test(self.test_generate_topics, "Generate Topics")

        # Test retrieving topics
        topics = self.run_test(self.test_get_topics, "Get Topics")

        # Test generating difficulties (only if we have topics)
        difficulties = self.run_test(self.test_generate_difficulties, "Generate Difficulties",
                                    skip_condition=not topics or len(topics) == 0)

        # Test retrieving difficulties
        difficulties = self.run_test(self.test_get_difficulties, "Get Difficulties")

        # Test storing seed questions
        seed_questions = self.run_test(self.test_store_seed_questions, "Store Seed Questions")

        # Test extracting seed questions
        extracted_questions = self.run_test(self.test_extract_seed_questions, "Extract Seed Questions")

        # Test retrieving seed questions
        seed_questions = self.run_test(self.test_get_seed_questions, "Get Seed Questions")

        # Test generating questions
        selected_topic = topics[0] if topics and len(topics) > 0 else None
        questions = self.run_test(
            lambda: self.test_generate_questions(selected_topic),
            "Generate Questions",
            skip_condition=not selected_topic
        )

        # Test retrieving questions
        questions = self.run_test(self.test_get_questions, "Get Questions")

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print a summary of all test results."""
        total = len(self.results)
        success_count = sum(1 for r in self.results if r["result_type"] == ResultType.SUCCESS)
        fail_count = sum(1 for r in self.results if r["result_type"] == ResultType.FAIL)
        skip_count = sum(1 for r in self.results if r["result_type"] == ResultType.SKIP)

        print("\n" + "=" * 50)
        print(f"{Colors.HEADER}Test Summary{Colors.ENDC}")
        print(f"Total tests: {total}")
        print(f"Successful: {Colors.GREEN}{success_count}{Colors.ENDC}")
        print(f"Failed: {Colors.FAIL}{fail_count}{Colors.ENDC}")
        print(f"Skipped: {Colors.WARNING}{skip_count}{Colors.ENDC}")
        print("=" * 50)

        if self.pack_id:
            print(f"\nPack ID: {self.pack_id}")
            print(f"You can continue testing this pack in the Swagger UI: {Colors.BLUE}http://localhost:8000/docs{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Test the Trivia API endpoints")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for the API")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--pack-id", help="Use an existing pack ID instead of creating a new one")
    args = parser.parse_args()

    tester = APITester(base_url=args.base_url, verbose=args.verbose)

    if args.pack_id:
        tester.pack_id = args.pack_id
        print(f"Using existing pack ID: {tester.pack_id}")

    tester.run_all_tests()

if __name__ == "__main__":
    main()