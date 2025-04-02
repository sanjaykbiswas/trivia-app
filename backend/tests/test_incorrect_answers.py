# test_incorrect_answers.py
#!/usr/bin/env python
# Example (topic provided): python3 tests/test_incorrect_answers.py --pack-name "Science Facts" --topic "Physics" -n 3 -v
# Example (topic generated): python3 tests/test_incorrect_answers.py --pack-name "Random Facts" -n 3 -v

import requests
import json
import argparse
import sys
import uuid
import time
from typing import Dict, List, Any, Optional
import os
import traceback
import random
from pathlib import Path # Added Path

# --- ADD THIS BLOCK ---
# Add the project root (backend/) to the Python path
script_path = Path(__file__).resolve()
project_root = script_path.parent.parent
sys.path.insert(0, str(project_root))
# --- END ADDED BLOCK ---

# Imports from src should now work (if any were needed)

# API base URL
BASE_URL = "http://localhost:8000/api"

# ANSI color codes
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

# Helper Functions (print_step, print_json, make_request)
def print_step(message: str):
    print(f"\n{Colors.HEADER}--- {message} ---{Colors.ENDC}")

def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    try:
        print(json.dumps(data, indent=2))
    except TypeError:
        print(str(data))

def make_request(method: str, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[requests.Response]:
    """Helper function to make API requests and handle basic errors."""
    url = f"{BASE_URL}{endpoint}"
    print(f"{Colors.CYAN}Requesting: {method.upper()} {url}{Colors.ENDC}")
    if params: print(f"Params: {params}")
    if json_data: print(f"Data:"); print_json(json_data)

    try:
        response = requests.request(method, url, json=json_data, params=params, timeout=120)
        print(f"Response Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"{Colors.WARNING}Response Content:{Colors.ENDC}")
            try: print_json(response.json())
            except json.JSONDecodeError: print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        return response
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}API request failed: {e}{Colors.ENDC}")
        return None

def create_or_get_pack(pack_name: str) -> Optional[str]:
    """Create a new pack or get ID if it exists."""
    print_step(f"Ensuring pack '{pack_name}' exists")
    list_response = make_request("GET", "/packs/")
    if list_response and list_response.status_code == 200:
        packs = list_response.json().get("packs", [])
        for p in packs:
            if p['name'].lower() == pack_name.lower():
                pack_id = p['id']
                print(f"{Colors.GREEN}Found existing pack '{pack_name}' with ID: {pack_id}{Colors.ENDC}")
                return pack_id
    data = {"name": pack_name, "description": "Test pack for incorrect answer generation", "price": 0.0, "creator_type": "system"}
    create_response = make_request("POST", "/packs/", json_data=data)
    if create_response and create_response.status_code == 201:
        pack_id = create_response.json().get("id")
        print(f"{Colors.GREEN}Successfully created pack '{pack_name}' with ID: {pack_id}{Colors.ENDC}")
        return pack_id
    else:
        print(f"{Colors.FAIL}Failed to create or find pack '{pack_name}'{Colors.ENDC}")
        return None

def generate_and_select_topic(pack_id: str) -> Optional[str]:
    """Generates topics for the pack and selects the first one."""
    print_step(f"Generating topics for pack {pack_id}")
    data = {"num_topics": 1}
    response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)
    if response and response.status_code == 200:
        topics = response.json().get("topics", [])
        if topics:
            selected_topic = topics[0]
            print(f"{Colors.GREEN}Successfully generated topics. Selected: '{selected_topic}'{Colors.ENDC}")
            return selected_topic
        else:
            print(f"{Colors.WARNING}Topic generation returned no topics.{Colors.ENDC}")
            return None
    else:
        print(f"{Colors.FAIL}Failed to generate topics.{Colors.ENDC}")
        return None

def add_topic_to_pack(pack_id: str, topic_name: str) -> bool:
    """Add a topic to the pack. Appends if topics exist."""
    print_step(f"Ensuring topic '{topic_name}' is in pack {pack_id}")
    get_response = make_request("GET", f"/packs/{pack_id}/topics/")
    existing_topics = []
    if get_response and get_response.status_code == 200:
        existing_topics = get_response.json().get("topics", [])
        print(f"Existing topics: {existing_topics}")
    if topic_name in existing_topics: print(f"Topic '{topic_name}' already exists in the pack. Skipping add."); return True
    endpoint = "/topics/"
    data = {"predefined_topic": topic_name}
    if existing_topics: print("Adding new topic to existing list using /additional endpoint."); endpoint = "/topics/additional"
    add_response = make_request("POST", f"/packs/{pack_id}{endpoint}", json_data=data)
    if add_response and add_response.status_code == 200:
        final_topics = add_response.json().get("topics", [])
        if topic_name in final_topics: print(f"{Colors.GREEN}Successfully added/confirmed topic '{topic_name}'{Colors.ENDC}"); return True
        else: print(f"{Colors.FAIL}Topic '{topic_name}' was not found in the final list after add attempt.{Colors.ENDC}"); return False
    else: print(f"{Colors.FAIL}Failed to add topic '{topic_name}'{Colors.ENDC}"); return False

def generate_pack_questions(pack_id: str, topic: str, num_questions: int, difficulty: str = "mixed") -> List[str]:
    """Generate questions for the specified topic."""
    print_step(f"Generating {num_questions} '{difficulty}' questions for topic '{topic}' in pack {pack_id}")
    data = {"pack_topic": topic, "difficulty": difficulty, "num_questions": num_questions, "debug_mode": False}
    response = make_request("POST", f"/packs/{pack_id}/questions/", json_data=data)
    if response and response.status_code == 200:
        questions_data = response.json().get("questions", [])
        question_ids = [q['id'] for q in questions_data]
        print(f"{Colors.GREEN}Successfully generated {len(questions_data)} questions.{Colors.ENDC}")
        global args # Access global args for verbose
        if args.verbose: print("Generated Questions:"); print_json(questions_data)
        return question_ids
    else:
        print(f"{Colors.FAIL}Failed to generate questions.{Colors.ENDC}")
        return []

def generate_incorrect_answers(pack_id: str, num_questions_generated: int) -> bool:
    """Trigger the batch generation of incorrect answers."""
    print_step(f"Triggering batch incorrect answer generation for pack {pack_id}")
    global args # Access global args for verbose
    params = {"num_answers": 3, "batch_size": 5, "debug_mode": args.verbose}
    response = make_request("POST", f"/packs/{pack_id}/questions/incorrect-answers/batch", params=params)
    if response and response.status_code == 200:
        result = response.json()
        processed_count = result.get("questions_processed", 0)
        status = result.get("status", "unknown")
        print(f"{Colors.GREEN}Batch incorrect answer generation completed.{Colors.ENDC}")
        print(f"  Status: {status}")
        print(f"  Questions Processed: {processed_count}")
        if processed_count >= num_questions_generated: print(f"{Colors.GREEN}Processed count matches or exceeds generated questions count.{Colors.ENDC}"); return True
        else: print(f"{Colors.WARNING}Processed count ({processed_count}) is less than generated questions ({num_questions_generated}). Check logs.{Colors.ENDC}"); return False
    else:
        print(f"{Colors.FAIL}Failed to generate incorrect answers in batch.{Colors.ENDC}")
        return False

def run_test_flow(args: argparse.Namespace):
    """Orchestrate the test steps."""
    pack_id = create_or_get_pack(args.pack_name)
    if not pack_id: return
    topic_to_use = args.topic
    if not topic_to_use:
        print(f"{Colors.CYAN}No topic provided, generating one...{Colors.ENDC}")
        topic_to_use = generate_and_select_topic(pack_id)
        if not topic_to_use: print(f"{Colors.FAIL}Stopping test because topic generation failed.{Colors.ENDC}"); return
    if not add_topic_to_pack(pack_id, topic_to_use): print(f"{Colors.FAIL}Stopping test because topic could not be added/confirmed.{Colors.ENDC}"); return
    print_step("Ensuring difficulty descriptions exist (generating if needed)")
    diff_resp = make_request("POST", f"/packs/{pack_id}/difficulties/", json_data={"force_regenerate": False})
    if not diff_resp or diff_resp.status_code != 200: print(f"{Colors.WARNING}Could not ensure difficulty descriptions exist. Question generation might use defaults.{Colors.ENDC}")
    generated_question_ids = generate_pack_questions(pack_id, topic_to_use, args.num_questions)
    if not generated_question_ids: print(f"{Colors.FAIL}Stopping test because question generation failed.{Colors.ENDC}"); return
    success = generate_incorrect_answers(pack_id, len(generated_question_ids))
    print("\n" + "="*30 + " Test Flow Summary " + "="*30)
    if success: print(f"{Colors.GREEN}Incorrect Answer Generation Test Flow Completed Successfully for pack '{args.pack_name}' (ID: {pack_id}) using topic '{topic_to_use}'.{Colors.ENDC}")
    else: print(f"{Colors.FAIL}Incorrect Answer Generation Test Flow Failed for pack '{args.pack_name}' (ID: {pack_id}) using topic '{topic_to_use}'.{Colors.ENDC}")
    print("="*80)

def main(args_parsed: argparse.Namespace):
    """Main execution function."""
    print(f"{Colors.BOLD}Starting Incorrect Answer Generation Test{Colors.ENDC}")
    print(f"Target API: {BASE_URL}")
    print(f"Pack Name: {args_parsed.pack_name}")
    if args_parsed.topic: print(f"Provided Topic: {args_parsed.topic}")
    else: print("Topic: Will be generated")
    print(f"Questions to Generate: {args_parsed.num_questions}")
    print("-" * 50)
    run_test_flow(args_parsed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Incorrect Answer Batch Generation API")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack (will create if not found)")
    parser.add_argument("--topic", "-t", help="Optional: Topic to generate questions for. If omitted, a topic will be generated.")
    parser.add_argument("--num-questions", "-n", type=int, default=3, help="Number of questions to generate before testing incorrect answers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    # Define args globally AFTER parsing
    args = parser.parse_args()
    main(args)