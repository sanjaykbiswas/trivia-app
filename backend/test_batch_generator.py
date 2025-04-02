#!/usr/bin/env python
# Example (topics provided, auto-instructions per topic):
# python3 test_batch_generator.py -p "World Geography Batch" -t "Capital Cities" "Major Rivers" -n 4 --difficulty easy medium -v
# Example (topics generated, auto-instructions per topic):
# python3 test_batch_generator.py -p "Random History Batch" --num-generated-topics 3 -n 5 --difficulty medium hard -v
# Example (disable auto-instructions):
# python3 test_batch_generator.py -p "SciFi Books Batch" --num-generated-topics 2 -n 3 --no-auto-instructions --difficulty easy hard expert -v

import requests
import json
import argparse
import sys
import uuid
import time
from typing import Dict, List, Any, Optional
import os
import traceback
import asyncio # Import asyncio

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

# --- Helper Functions (print_step, print_json, make_request, create_or_get_pack, add_provided_topics_to_pack, generate_api_topics, generate_difficulties, process_seed_questions) ---
# (These helpers remain largely unchanged)

def print_step(message: str):
    print(f"\n{Colors.HEADER}--- {message} ---{Colors.ENDC}")

def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    try:
        print(json.dumps(data, indent=2))
    except TypeError:
        print(str(data))

def make_request(method: str, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 300) -> Optional[requests.Response]:
    """Helper function to make API requests and handle basic errors."""
    url = f"{BASE_URL}{endpoint}"
    print(f"{Colors.CYAN}Requesting: {method.upper()} {url}{Colors.ENDC}")
    if params:
        print(f"Params: {params}")
    if json_data:
        print(f"Data:")
        print_json(json_data)

    try:
        response = requests.request(method, url, json=json_data, params=params, timeout=timeout)
        print(f"Response Status: {response.status_code}")
        global args # Access global args
        if response.status_code >= 400 or (args and args.verbose):
             print(f"{Colors.WARNING if response.status_code >= 400 else Colors.CYAN}Response Content:{Colors.ENDC}")
             try:
                 print_json(response.json())
             except json.JSONDecodeError:
                 print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
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

    data = {"name": pack_name, "description": f"Test pack for batch generation", "price": 0.0, "creator_type": "system"}
    create_response = make_request("POST", "/packs/", json_data=data)
    if create_response and create_response.status_code == 201:
        pack_id = create_response.json().get("id")
        print(f"{Colors.GREEN}Successfully created pack '{pack_name}' with ID: {pack_id}{Colors.ENDC}")
        return pack_id
    else:
        print(f"{Colors.FAIL}Failed to create or find pack '{pack_name}'. Status: {create_response.status_code if create_response else 'N/A'}{Colors.ENDC}")
        return None

def add_provided_topics_to_pack(pack_id: str, topics: List[str]) -> bool:
    """Adds multiple specific topics (provided by user) to a pack."""
    print_step(f"Adding {len(topics)} user-provided topics to pack {pack_id}")
    if not topics:
        print(f"{Colors.WARNING}No topics provided to add.{Colors.ENDC}")
        return False

    all_added = True
    current_topics = []

    # Get existing topics first
    get_response = make_request("GET", f"/packs/{pack_id}/topics/")
    if get_response and get_response.status_code == 200:
        current_topics = get_response.json().get("topics", [])
        print(f"  Existing topics: {current_topics}")

    topics_to_add = [t for t in topics if t not in current_topics]
    if not topics_to_add:
        print(f"{Colors.GREEN}All specified topics already exist in the pack.{Colors.ENDC}")
        return True

    # Add the first *new* topic using the main endpoint if no topics existed before
    start_index = 0
    if not current_topics and topics_to_add:
        first_new_topic = topics_to_add[0]
        print(f"  Adding first new topic: '{first_new_topic}' using /topics/")
        data = {"predefined_topic": first_new_topic}
        response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)
        if response and response.status_code == 200:
            current_topics = response.json().get("topics", []) # Update current topics
            if first_new_topic not in current_topics:
                print(f"{Colors.FAIL}  Failed to add first new topic '{first_new_topic}'{Colors.ENDC}")
                all_added = False
            else:
                 print(f"{Colors.GREEN}  Added '{first_new_topic}'. Current topics: {current_topics}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}  Failed initial topic add request for '{first_new_topic}'{Colors.ENDC}")
            all_added = False
        start_index = 1 # Move to the next topic

    # Add remaining new topics using the additional endpoint
    for topic in topics_to_add[start_index:]:
        print(f"  Adding additional topic: '{topic}' using /topics/additional")
        data = {"predefined_topic": topic}
        response = make_request("POST", f"/packs/{pack_id}/topics/additional", json_data=data)
        if response and response.status_code == 200:
             current_topics = response.json().get("topics", []) # Update current topics
             if topic not in current_topics:
                 print(f"{Colors.FAIL}  Failed to add additional topic '{topic}'{Colors.ENDC}")
                 all_added = False
             else:
                  print(f"{Colors.GREEN}  Added '{topic}'. Current topics: {current_topics}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}  Failed additional topic add request for '{topic}'{Colors.ENDC}")
            all_added = False
        time.sleep(0.2) # Slight delay between API calls

    return all_added

def generate_api_topics(pack_id: str, num_topics: int) -> Optional[List[str]]:
    """Generates topics using the API endpoint."""
    print_step(f"Generating {num_topics} topics via API for pack {pack_id}")
    data = {"num_topics": num_topics}
    response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)
    if response and response.status_code == 200:
        generated_topics = response.json().get("topics", [])
        if generated_topics:
            print(f"{Colors.GREEN}Successfully generated {len(generated_topics)} topics via API:{Colors.ENDC}")
            for t in generated_topics: print(f"  - {t}")
            return generated_topics
    print(f"{Colors.FAIL}Failed to generate topics via API.{Colors.ENDC}")
    return None

def generate_difficulties(pack_id: str) -> bool:
    """Generate difficulty descriptions for a pack."""
    print_step(f"Generating/Ensuring difficulty descriptions for pack {pack_id}")
    data = {"force_regenerate": False} # Don't force unless needed
    response = make_request("POST", f"/packs/{pack_id}/difficulties/", json_data=data)
    if response and response.status_code == 200:
        print(f"{Colors.GREEN}Successfully generated/ensured difficulty descriptions{Colors.ENDC}")
        return True
    print(f"{Colors.FAIL}Failed to generate difficulty descriptions.{Colors.ENDC}")
    return False

def process_seed_questions(pack_id: str, seed_questions_file: Optional[str]) -> bool:
    """Process seed questions from a file, if provided."""
    if not seed_questions_file:
        print(f"{Colors.CYAN}No seed questions file provided, skipping.{Colors.ENDC}")
        return True

    if not os.path.exists(seed_questions_file):
        print(f"{Colors.FAIL}Seed questions file not found: {seed_questions_file}{Colors.ENDC}")
        return False

    print_step(f"Processing seed questions from {seed_questions_file}")
    try:
        with open(seed_questions_file, 'r') as f: seed_content = f.read()
        data = {"text_content": seed_content}
        response = make_request("POST", f"/packs/{pack_id}/questions/seed/extract", json_data=data)
        if response and response.status_code == 200:
            count = response.json().get("count", 0)
            print(f"{Colors.GREEN}Successfully extracted and stored {count} seed questions{Colors.ENDC}")
            return True
    except Exception as e:
        print(f"{Colors.FAIL}Error processing seed questions file: {str(e)}{Colors.ENDC}")
        print(traceback.format_exc())

    print(f"{Colors.FAIL}Failed to extract/store seed questions.{Colors.ENDC}")
    return False


# --- REMOVED handle_custom_instructions function ---
# This logic is now handled within the QuestionService


def trigger_batch_question_generation(pack_id: str, topic_configs: List[Dict], regenerate_instructions: bool, debug_mode: bool) -> Optional[Dict[str, Any]]:
    """Trigger the batch question generation and incorrect answer process."""
    num_configs = sum(len(tc.get("difficulty_configs", [])) for tc in topic_configs)
    print_step(f"Triggering batch question generation for {len(topic_configs)} topics across {num_configs} difficulty configs")
    # --- MODIFIED Data payload ---
    data = {
        "topic_configs": topic_configs,
        "regenerate_instructions": regenerate_instructions, # Pass flag
        "debug_mode": debug_mode
        }
    # --- END MODIFIED Data ---
    response = make_request("POST", f"/packs/{pack_id}/questions/batch-generate", json_data=data, timeout=900) # Increased timeout further
    if response and response.status_code == 200:
        result = response.json()
        print(f"{Colors.GREEN}Batch generation request completed.{Colors.ENDC}")
        print(f"  Status: {result.get('status', 'UNKNOWN')}")
        print(f"  Topics Processed (>=1 success): {len(result.get('topics_processed', []))}")
        print(f"  Total Questions Generated: {result.get('total_questions_generated', 0)}")
        if result.get('errors'): print(f"{Colors.WARNING}  Errors occurred for topics (>=1 failure): {result['errors']}{Colors.ENDC}")
        return result
    print(f"{Colors.FAIL}Batch generation request failed. Status: {response.status_code if response else 'N/A'}{Colors.ENDC}")
    return None

# --- verify_questions_exist function remains unchanged ---
def verify_questions_exist(pack_id: str, expected_topics: List[str], expected_total_questions: int, batch_result: Optional[Dict]) -> bool:
    """Verify if questions were created, considering the batch status."""
    if not batch_result:
        print_step(f"Verifying question creation for pack {pack_id} (Batch Request Failed)")
        print(f"{Colors.FAIL}Verification skipped as batch request failed.{Colors.ENDC}")
        return False

    batch_status = batch_result.get('status', 'failed')
    actual_generated_count = batch_result.get('total_questions_generated', 0)
    processed_topics = batch_result.get('topics_processed', [])
    failed_topics_reported = batch_result.get('errors') # Get errors, could be None

    print_step(f"Verifying question creation for pack {pack_id} (Batch Status: {batch_status})")

    # Fetch questions from API to double-check
    params = {"limit": expected_total_questions + 50} # Fetch more than expected
    response = make_request("GET", f"/packs/{pack_id}/questions/", params=params)
    api_found_questions = []
    api_found_topics = set()
    api_found_count = 0
    if response and response.status_code == 200:
        api_found_questions = response.json().get("questions", [])
        api_found_count = len(api_found_questions)
        api_found_topics = {q.get("pack_topics_item") for q in api_found_questions if q.get("pack_topics_item")}
        print(f"  API check found {api_found_count} questions in total.")
        print(f"  API check found topics: {api_found_topics}")
    else:
        print(f"{Colors.WARNING}  API check failed to retrieve questions. Relying solely on batch response.{Colors.ENDC}")

    # --- Verification Logic ---
    success = True
    expected_topics_lower = {t.lower() for t in expected_topics}
    processed_topics_lower = {t.lower() for t in processed_topics}

    failed_topics_reported_lower = set()
    if failed_topics_reported is not None: # Check if it's not None
        failed_topics_reported_lower = {t.lower() for t in failed_topics_reported}


    if batch_status == "completed":
        print("  Checking 'completed' status...")
        if actual_generated_count < expected_total_questions:
            success = False
            print(f"{Colors.FAIL}  Mismatch: Status 'completed' but batch reported fewer questions ({actual_generated_count}) than expected ({expected_total_questions}).{Colors.ENDC}")
        if api_found_count != actual_generated_count:
             print(f"{Colors.WARNING}  API Count Mismatch: Batch reported {actual_generated_count} generated, but API found {api_found_count}.{Colors.ENDC}")

        # All expected topics should be in processed_topics
        missing_processed = expected_topics_lower - processed_topics_lower
        if missing_processed:
            success = False
            print(f"{Colors.FAIL}  Mismatch: Status 'completed' but expected topics missing from 'topics_processed': {missing_processed}{Colors.ENDC}")

        if failed_topics_reported is not None: # Check for None explicitly
            success = False
            print(f"{Colors.FAIL}  Mismatch: Status 'completed' but 'errors' list is not null/empty: {failed_topics_reported}{Colors.ENDC}")

    elif batch_status == "partial_failure":
        print("  Checking 'partial_failure' status...")
        if actual_generated_count == 0 and expected_total_questions > 0:
            print(f"{Colors.WARNING}  Status 'partial_failure' but 0 questions generated by batch.{Colors.ENDC}")
        elif actual_generated_count >= expected_total_questions:
             print(f"{Colors.WARNING}  Status 'partial_failure' but batch reported generating all/more ({actual_generated_count}) questions than expected ({expected_total_questions}).{Colors.ENDC}")

        if failed_topics_reported is None: # Check for None explicitly
             print(f"{Colors.WARNING}  Mismatch: Status 'partial_failure' but 'errors' list is null/missing.{Colors.ENDC}")
        if not processed_topics and actual_generated_count > 0:
             print(f"{Colors.WARNING}  Mismatch: Status 'partial_failure' with questions generated ({actual_generated_count}), but 'topics_processed' list is empty.{Colors.ENDC}")

        if api_found_count != actual_generated_count:
            print(f"{Colors.WARNING}  API Count Mismatch: Batch reported {actual_generated_count} generated, but API found {api_found_count}.{Colors.ENDC}")

    elif batch_status == "failed":
        print("  Checking 'failed' status...")
        if actual_generated_count > 0:
            success = False
            print(f"{Colors.FAIL}  Mismatch: Status 'failed' but batch reported {actual_generated_count} questions generated.{Colors.ENDC}")
        if api_found_count > 0:
             print(f"{Colors.WARNING}  API Count Mismatch: Status 'failed' but API found {api_found_count} questions.{Colors.ENDC}")
        if processed_topics:
            success = False
            print(f"{Colors.FAIL}  Mismatch: Status 'failed' but 'topics_processed' is not empty: {processed_topics}{Colors.ENDC}")

    else: # Unknown status
        success = False
        print(f"{Colors.FAIL}  Unknown batch status reported: '{batch_status}'. Verification failed.{Colors.ENDC}")


    if success:
        print(f"{Colors.GREEN}Verification check passed for batch status '{batch_status}'.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}Verification check failed for batch status '{batch_status}'.{Colors.ENDC}")

    return success

# --- Main Test Flow ---
def run_batch_test_flow(args: argparse.Namespace):
    """Orchestrate the batch test steps."""
    pack_id = create_or_get_pack(args.pack_name)
    if not pack_id: return

    topics_to_use = []
    if args.topics:
        print(f"{Colors.CYAN}Using provided topics: {args.topics}{Colors.ENDC}")
        if not add_provided_topics_to_pack(pack_id, args.topics): print(f"{Colors.FAIL}Stopping test: provided topics not added.{Colors.ENDC}"); return
        topics_to_use = args.topics
    else:
        print(f"{Colors.CYAN}No topics provided, generating {args.num_generated_topics} via API...{Colors.ENDC}")
        generated_topics = generate_api_topics(pack_id, args.num_generated_topics)
        if not generated_topics: print(f"{Colors.FAIL}Stopping test: API topic generation failed.{Colors.ENDC}"); return
        topics_to_use = generated_topics
    if not topics_to_use: print(f"{Colors.FAIL}No topics available. Exiting.{Colors.ENDC}"); return

    if not generate_difficulties(pack_id): print(f"{Colors.WARNING}Failed generating difficulties, continuing cautiously...{Colors.ENDC}")
    process_seed_questions(pack_id, args.seed_questions)

    # --- REMOVED Pre-generation of custom instructions ---
    # topic_instructions_map = handle_custom_instructions(pack_id, args, topics_to_use)

    # Prepare topic configurations for the batch request
    topic_configs = []
    expected_total_questions = 0
    for topic in topics_to_use:
        difficulty_configs = []
        # --- REMOVED fetching instruction from pre-generated map ---
        # topic_instructions = topic_instructions_map.get(topic)

        for diff_level in args.difficulty:
            difficulty_configs.append({"difficulty": diff_level, "num_questions": args.num_questions_per_difficulty})
            expected_total_questions += args.num_questions_per_difficulty

        topic_configs.append({
            "topic": topic,
            "difficulty_configs": difficulty_configs,
            # --- REMOVED passing instruction override here ---
            # custom_instructions": topic_instructions # Let service handle fetching/generation
        })

    # Trigger batch generation
    # --- Pass regenerate_instructions flag ---
    batch_result = trigger_batch_question_generation(
        pack_id,
        topic_configs,
        args.regenerate_instructions, # Pass flag
        args.debug
        )
    # --- END Pass flag ---

    # Verify results based on batch status
    verification_passed = verify_questions_exist(pack_id, topics_to_use, expected_total_questions, batch_result)

    # --- Final Summary ---
    print("\n" + "="*30 + " Batch Test Flow Summary " + "="*30)
    final_outcome = Colors.FAIL + "FAILED" + Colors.ENDC
    if batch_result:
        status = batch_result.get("status", "failed").lower()
        if status == "completed" and verification_passed:
            final_outcome = Colors.GREEN + "SUCCESS" + Colors.ENDC
        elif status == "partial_failure" and verification_passed:
             # Partial failure is acceptable if verification aligns
             final_outcome = Colors.WARNING + "PARTIAL SUCCESS (Verification OK)" + Colors.ENDC
        elif status == "failed" and verification_passed:
             # Failed status verified (e.g., 0 questions generated)
             final_outcome = Colors.GREEN + "SUCCESS (Failed status verified)" + Colors.ENDC
        elif not verification_passed:
             final_outcome = Colors.FAIL + f"FAILED (Verification Mismatch for Status '{status}')" + Colors.ENDC
        # Add case for unknown status if needed
    else: # Batch request itself failed
         final_outcome = Colors.FAIL + "FAILED (Batch Request Error)" + Colors.ENDC

    print(f"Overall Test Result: {final_outcome}")
    print(f"  Pack ID: {pack_id}")
    print(f"  Topics Used: {topics_to_use}")
    print(f"  Difficulties Tested per Topic: {args.difficulty}")
    print(f"  Expected Total Questions: {expected_total_questions}")
    # --- MODIFIED Summary Output ---
    print(f"  Custom Instructions: {'Generated within batch call' if args.auto_generate_instructions else 'Disabled'}")
    print(f"    Forced Regeneration: {'YES' if args.regenerate_instructions else 'NO'}")
    # --- END MODIFIED Summary Output ---
    if batch_result:
        print(f"  Batch Request Status: {batch_result.get('status', 'N/A')}")
        print(f"  Reported Questions Generated: {batch_result.get('total_questions_generated', 'N/A')}")
        print(f"  Reported Success Topics: {batch_result.get('topics_processed', [])}")
        if batch_result.get('errors'): print(f"  Reported Failed Topics: {batch_result['errors']}")
    print(f"  Final Verification Check Passed: {verification_passed}")
    print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Test Multi-Difficulty Batch Trivia Question Generation API")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack (will create if not found)")
    parser.add_argument("--topics", "-t", nargs='*', help="List of topics. If omitted, topics will be generated.")
    parser.add_argument("--num-generated-topics", type=int, default=2, help="Number of topics to generate if --topics is omitted.")
    parser.add_argument("--difficulty", "-d", nargs='*', choices=["easy", "medium", "hard", "expert", "mixed"],
                      default=["medium"], help="List of difficulty levels to generate for EACH topic (default: medium)")
    parser.add_argument("--num-questions-per-difficulty", "-n", type=int, default=3,
                      help="Number of questions per difficulty level per topic")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions")
    # --- REMOVED save_generated_instructions flag ---
    # --- UPDATED instruction flags ---
    parser.add_argument("--no-auto-instructions", action="store_false", dest="auto_generate_instructions",
                        help="Disable automatic generation of custom instructions per topic (default: ON within batch call)")
    parser.add_argument("--regenerate-instructions", action="store_true",
                        help="Force regeneration of custom instructions during the batch call, even if they exist.")
    parser.set_defaults(auto_generate_instructions=True, regenerate_instructions=False)
    # --- END UPDATED instruction flags ---
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for API calls")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode in the API request payload")

    # Access args globally for make_request logging
    global args
    args = parser.parse_args()

    # Validation
    if not args.topics and args.num_generated_topics <= 0: parser.error("If --topics not provided, --num-generated-topics must be > 0.")
    if not args.difficulty: args.difficulty = ["medium"] # Ensure default if user provides empty list

    # File existence checks
    if args.seed_questions and not os.path.exists(args.seed_questions): print(f"{Colors.FAIL}Seed questions file not found: {args.seed_questions}{Colors.ENDC}"); sys.exit(1)

    run_batch_test_flow(args)

if __name__ == "__main__":
    main()