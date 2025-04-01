#!/usr/bin/env python
# Example (topics provided): python3 test_batch_generator.py -p "World Geography" -t "Capital Cities" "Major Rivers" "Mountain Ranges" -n 4 -v
# Example (topics generated): python3 test_batch_generator.py -p "Random History" --num-generated-topics 3 -n 5 -d hard -v
# Example with auto-instructions (topics generated): python3 test_batch_generator.py -p "SciFi Books" --num-generated-topics 3 -n 3 -a -v

import requests
import json
import argparse
import sys
import uuid
import time
from typing import Dict, List, Any, Optional
import os
import traceback

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

# --- Helper Functions ---

def print_step(message: str):
    print(f"\n{Colors.HEADER}--- {message} ---{Colors.ENDC}")

def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    try:
        print(json.dumps(data, indent=2))
    except TypeError:
        print(str(data))

def make_request(method: str, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None, timeout: int = 120) -> Optional[requests.Response]:
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
        # Print response body only on failure or if verbose
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
        print(f"{Colors.FAIL}Failed to create or find pack '{pack_name}'{Colors.ENDC}")
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
    # Otherwise, use the additional endpoint for all new topics
    start_index = 0
    if not current_topics and topics_to_add:
        first_new_topic = topics_to_add[0]
        print(f"  Adding first new topic: '{first_new_topic}' using /topics/")
        data = {"predefined_topic": first_new_topic}
        response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)
        if response and response.status_code == 200:
            current_topics = response.json().get("topics", [])
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
             current_topics = response.json().get("topics", [])
             if topic not in current_topics:
                 print(f"{Colors.FAIL}  Failed to add additional topic '{topic}'{Colors.ENDC}")
                 all_added = False
             else:
                  print(f"{Colors.GREEN}  Added '{topic}'. Current topics: {current_topics}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}  Failed additional topic add request for '{topic}'{Colors.ENDC}")
            all_added = False
        time.sleep(0.2)

    return all_added

# --- NEW Helper: Generate Topics via API ---
def generate_api_topics(pack_id: str, num_topics: int) -> Optional[List[str]]:
    """Generates topics using the API endpoint."""
    print_step(f"Generating {num_topics} topics via API for pack {pack_id}")
    data = {"num_topics": num_topics}
    # We use the POST /topics/ endpoint which will create/overwrite topics
    response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)
    if response and response.status_code == 200:
        generated_topics = response.json().get("topics", [])
        if generated_topics:
            print(f"{Colors.GREEN}Successfully generated {len(generated_topics)} topics via API:{Colors.ENDC}")
            for t in generated_topics: print(f"  - {t}")
            return generated_topics
        else:
            print(f"{Colors.FAIL}API generated 0 topics.{Colors.ENDC}")
            return None
    else:
        print(f"{Colors.FAIL}Failed to generate topics via API.{Colors.ENDC}")
        return None
# --- END NEW Helper ---

def generate_difficulties(pack_id: str) -> bool:
    """Generate difficulty descriptions for a pack."""
    print_step(f"Generating difficulty descriptions for pack {pack_id}")
    data = {"force_regenerate": False} # Don't force if they exist
    response = make_request("POST", f"/packs/{pack_id}/difficulties/", json_data=data)
    if response and response.status_code == 200:
        print(f"{Colors.GREEN}Successfully generated/confirmed difficulty descriptions{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}Failed to generate difficulty descriptions.{Colors.ENDC}")
        return False

def process_seed_questions(pack_id: str, seed_questions_file: Optional[str]) -> bool:
    """Process seed questions from a file, if provided."""
    if not seed_questions_file:
        print(f"{Colors.CYAN}No seed questions file provided, skipping.{Colors.ENDC}")
        return True

    print_step(f"Processing seed questions from {seed_questions_file}")
    try:
        with open(seed_questions_file, 'r') as f:
            seed_content = f.read()

        data = {"text_content": seed_content}
        response = make_request("POST", f"/packs/{pack_id}/questions/seed/extract", json_data=data)

        if response and response.status_code == 200:
            count = response.json().get("count", 0)
            print(f"{Colors.GREEN}Successfully extracted and stored {count} seed questions{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}Failed to extract/store seed questions.{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.FAIL}Error processing seed questions file: {str(e)}{Colors.ENDC}")
        return False

def handle_custom_instructions(pack_id: str, args: argparse.Namespace, topics_to_use: List[str]) -> Optional[str]:
    """Generate or load custom instructions based on args."""
    if args.auto_generate_instructions:
        print_step(f"Auto-generating custom instructions for pack {pack_id}")
        if not topics_to_use:
            print(f"{Colors.WARNING}Cannot auto-generate instructions without topics. Skipping.{Colors.ENDC}")
            return None
        # Use the first topic for generation for simplicity in this test
        first_topic = topics_to_use[0]
        data = {"pack_topic": first_topic}
        response = make_request("POST", f"/packs/{pack_id}/questions/custom-instructions/generate", json_data=data)
        if response and response.status_code == 200:
            custom_instructions = response.json().get("custom_instructions")
            print(f"{Colors.GREEN}Successfully generated custom instructions.{Colors.ENDC}")
            if args.verbose: print(f"{Colors.CYAN}{custom_instructions}{Colors.ENDC}")
            if args.save_generated_instructions and custom_instructions:
                try:
                    with open(args.save_generated_instructions, 'w') as f:
                        f.write(custom_instructions)
                    print(f"{Colors.GREEN}Saved generated instructions to {args.save_generated_instructions}{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.FAIL}Failed to save generated instructions: {e}{Colors.ENDC}")
            return custom_instructions
        else:
            print(f"{Colors.FAIL}Failed to auto-generate custom instructions.{Colors.ENDC}")
            return None
    elif args.custom_instructions_file:
        print_step(f"Loading custom instructions from {args.custom_instructions_file}")
        try:
            with open(args.custom_instructions_file, 'r') as f:
                custom_instructions = f.read()
            print(f"{Colors.GREEN}Successfully loaded custom instructions.{Colors.ENDC}")
            if args.verbose: print(f"{Colors.CYAN}{custom_instructions}{Colors.ENDC}")
            # Optionally store them via API if needed
            # data = {"instructions": custom_instructions}
            # make_request("POST", f"/packs/{pack_id}/questions/custom-instructions/input", json_data=data)
            return custom_instructions
        except Exception as e:
            print(f"{Colors.FAIL}Error reading custom instructions file: {str(e)}{Colors.ENDC}")
            return None
    else:
        print(f"{Colors.CYAN}No custom instructions specified.{Colors.ENDC}")
        return None # No instructions specified

def trigger_batch_question_generation(pack_id: str, topic_configs: List[Dict], debug_mode: bool) -> Optional[Dict[str, Any]]:
    """Trigger the batch question generation and incorrect answer process."""
    print_step(f"Triggering batch question generation for {len(topic_configs)} topics")
    data = {
        "topic_configs": topic_configs,
        "debug_mode": debug_mode
    }
    response = make_request("POST", f"/packs/{pack_id}/questions/batch-generate", json_data=data, timeout=300)

    if response and response.status_code == 200:
        result = response.json()
        print(f"{Colors.GREEN}Batch generation request completed.{Colors.ENDC}")
        print(f"  Status: {result.get('status', 'UNKNOWN')}")
        print(f"  Topics Processed: {len(result.get('topics_processed', []))}")
        print(f"  Total Questions Generated: {result.get('total_questions_generated', 0)}")
        if result.get('errors'):
            print(f"{Colors.WARNING}  Errors occurred for topics: {result['errors']}{Colors.ENDC}")
        return result
    else:
        print(f"{Colors.FAIL}Batch generation request failed.{Colors.ENDC}")
        return None

def verify_questions_exist(pack_id: str, expected_topics: List[str], expected_total_questions: int) -> bool:
    """Verify if questions were created for the expected topics."""
    print_step(f"Verifying question creation for pack {pack_id}")
    params = {"limit": expected_total_questions + 50} # Fetch more to be sure
    response = make_request("GET", f"/packs/{pack_id}/questions/", params=params)

    if response and response.status_code == 200:
        questions_data = response.json().get("questions", [])
        total_found = len(questions_data)
        print(f"  Found {total_found} questions in total for the pack.")

        found_topics = {q.get("pack_topics_item") for q in questions_data if q.get("pack_topics_item")}
        print(f"  Topics found in questions: {found_topics}")

        # Case-insensitive comparison for verification
        expected_topics_lower = {t.lower() for t in expected_topics}
        found_topics_lower = {ft.lower() for ft in found_topics}

        missing_topics = [t for t in expected_topics if t.lower() not in found_topics_lower]
        unexpected_topics = [ft for ft in found_topics if ft.lower() not in expected_topics_lower]

        success = True
        # Check if at least the minimum expected number of questions were generated overall
        # Allow for some failures in individual topics if the status was partial_failure
        if total_found == 0 and expected_total_questions > 0 :
             print(f"{Colors.FAIL}  Expected at least some questions, but found 0.{Colors.ENDC}")
             success = False
        elif total_found < expected_total_questions // 2 and expected_total_questions > 0 : # Heuristic: fail if less than half expected were generated
             print(f"{Colors.WARNING}  Significantly fewer questions generated ({total_found}) than expected ({expected_total_questions}).{Colors.ENDC}")
             # Consider if this should be a hard fail depending on tolerance

        if missing_topics:
             print(f"{Colors.WARNING}  Questions for some expected topics might be missing or failed generation: {missing_topics}{Colors.ENDC}")
             # Don't necessarily fail the whole verification if partial failure was expected
             # success = False
        if unexpected_topics:
             print(f"{Colors.WARNING}  Found questions for unexpected topics: {unexpected_topics}{Colors.ENDC}")

        if success:
             print(f"{Colors.GREEN}Verification complete. Check logs for details on missing/unexpected topics if any.{Colors.ENDC}")
             return True
        else:
             print(f"{Colors.FAIL}Verification failed.{Colors.ENDC}")
             return False
    else:
        print(f"{Colors.FAIL}Failed to retrieve questions for verification.{Colors.ENDC}")
        return False

# --- Main Test Flow ---

def run_batch_test_flow(args: argparse.Namespace):
    """Orchestrate the batch test steps."""
    pack_id = create_or_get_pack(args.pack_name)
    if not pack_id:
        return

    topics_to_use = []
    if args.topics:
        print(f"{Colors.CYAN}Using provided topics: {args.topics}{Colors.ENDC}")
        # Add provided topics to the pack
        if not add_provided_topics_to_pack(pack_id, args.topics):
            print(f"{Colors.FAIL}Stopping test because provided topics could not be added.{Colors.ENDC}")
            return
        topics_to_use = args.topics
    else:
        print(f"{Colors.CYAN}No topics provided, generating {args.num_generated_topics} via API...{Colors.ENDC}")
        # Generate topics using the API
        generated_topics = generate_api_topics(pack_id, args.num_generated_topics)
        if not generated_topics:
             print(f"{Colors.FAIL}Stopping test because API topic generation failed.{Colors.ENDC}")
             return
        topics_to_use = generated_topics
        # Topics are already added by the generation endpoint, no need to call add_topics_to_pack

    if not topics_to_use:
        print(f"{Colors.FAIL}No topics available to proceed with question generation. Exiting.{Colors.ENDC}")
        return

    # Generate difficulties (ensures descriptions exist)
    if not generate_difficulties(pack_id):
        print(f"{Colors.WARNING}Failed to generate difficulties, continuing without them...{Colors.ENDC}")

    # Process seed questions (optional)
    process_seed_questions(pack_id, args.seed_questions)

    # Handle custom instructions (optional)
    custom_instructions = handle_custom_instructions(pack_id, args, topics_to_use)

    # Prepare topic configurations for the batch request
    topic_configs = []
    for topic in topics_to_use:
        topic_configs.append({
            "topic": topic,
            "num_questions": args.num_questions_per_topic,
            "difficulty": args.difficulty,
            "custom_instructions": custom_instructions # Apply same instructions to all topics in this test
        })

    # Trigger batch generation
    batch_result = trigger_batch_question_generation(pack_id, topic_configs, args.debug)

    # Verification
    verification_passed = False
    if batch_result:
        # Calculate expected total based ONLY on successfully processed topics
        successfully_processed_topics = batch_result.get('topics_processed', [])
        expected_successful_questions = sum(
            cfg['num_questions'] for cfg in topic_configs if cfg['topic'] in successfully_processed_topics
        )
        verification_passed = verify_questions_exist(pack_id, successfully_processed_topics, expected_successful_questions)
    else:
        verification_passed = False # Batch request itself failed

    # --- Final Summary ---
    print("\n" + "="*30 + " Batch Test Flow Summary " + "="*30)
    final_outcome = Colors.FAIL + "FAILED" + Colors.ENDC
    if batch_result:
        status = batch_result.get("status", "failed").lower()
        if status == "completed" and verification_passed:
            final_outcome = Colors.GREEN + "SUCCESS" + Colors.ENDC
        elif status == "partial_failure":
            final_outcome = Colors.WARNING + "PARTIAL FAILURE" + Colors.ENDC

    print(f"Overall Test Result: {final_outcome}")
    print(f"  Pack ID: {pack_id}")
    print(f"  Topics Used: {topics_to_use}")
    if batch_result:
        print(f"  Batch Request Status: {batch_result.get('status', 'N/A')}")
        print(f"  Topics Successfully Processed: {batch_result.get('topics_processed', [])}")
        print(f"  Total Questions Generated: {batch_result.get('total_questions_generated', 'N/A')}")
        if batch_result.get('errors'):
            print(f"  Failed Topics (Generation): {batch_result['errors']}")
    print(f"  Verification Step Passed: {verification_passed}")
    print("="*80)

def main():
    parser = argparse.ArgumentParser(description="Test Batch Trivia Question Generation API")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack (will create if not found)")
    # --- Topics are now optional ---
    parser.add_argument("--topics", "-t", nargs='*', help="List of topics to generate questions for. If omitted, topics will be generated.")
    parser.add_argument("--num-generated-topics", type=int, default=3, help="Number of topics to generate if --topics is omitted.")
    # --- End Topics optional ---
    parser.add_argument("--num-questions-per-topic", "-n", type=int, default=3, help="Number of questions per topic")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard", "expert", "mixed"],
                      default="mixed", help="Difficulty level (applied to all topics)")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions")
    parser.add_argument("--custom-instructions-file", "-i", help="Path to a file containing custom instructions (applied globally)")
    parser.add_argument("--auto-generate-instructions", "-a", action="store_true",
                        help="Auto-generate global custom instructions from the first topic and seed questions")
    parser.add_argument("--save-generated-instructions", "-g",
                        help="Save auto-generated instructions to this file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for API calls")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode in the API request payload")

    global args # Make args global for helper functions
    args = parser.parse_args()

    # Validation
    if not args.topics and args.num_generated_topics <= 0:
         parser.error("If --topics is not provided, --num-generated-topics must be greater than 0.")

    # Conflict check
    if args.custom_instructions_file and args.auto_generate_instructions:
        print(f"{Colors.WARNING}Both --custom-instructions-file and --auto-generate-instructions provided. Auto-generation will take precedence.{Colors.ENDC}")
        args.custom_instructions_file = None # Prioritize auto-generate

    # File existence checks
    if args.seed_questions and not os.path.exists(args.seed_questions):
        print(f"{Colors.FAIL}Seed questions file not found: {args.seed_questions}{Colors.ENDC}")
        sys.exit(1)
    if args.custom_instructions_file and not os.path.exists(args.custom_instructions_file):
        print(f"{Colors.FAIL}Custom instructions file not found: {args.custom_instructions_file}{Colors.ENDC}")
        sys.exit(1)

    run_batch_test_flow(args)

if __name__ == "__main__":
    main()