# python3 test_generator.py --pack-name "Book Title Adjectives" --topic "Book Title Adjectives" --seed-questions seed_questions.txt -a -g generated_instruction.txt -v
# python3 test_generator.py --pack-name "Physics Concepts" --topic "Quantum Mechanics" -n 10 -d hard -a

#!/usr/bin/env python
import requests
import json
import argparse
import sys
from typing import Dict, List, Any, Optional
import os
import traceback # Added traceback

# API base URL
BASE_URL = "http://localhost:8000/api"

# ANSI color codes for prettier output
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

def print_json(data: Any) -> None:
    """Pretty print JSON data."""
    try:
        print(json.dumps(data, indent=2))
    except TypeError:
        print(str(data))

def print_step(message: str):
    print(f"\n{Colors.HEADER}--- {message} ---{Colors.ENDC}")

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
        # Access global args to check verbose flag
        global args
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


def create_pack(name: str, description: str = None) -> Optional[str]:
    """Create a new pack and return its ID."""
    data = {
        "name": name,
        "description": description or f"Custom pack created for testing",
        "price": 0.0,
        "creator_type": "system"
    }

    print_step(f"Creating pack: {name}")
    response = make_request("POST", "/packs/", json_data=data)

    if response and response.status_code == 201:
        pack_data = response.json()
        pack_id = pack_data.get("id")
        print(f"{Colors.GREEN}Successfully created pack with ID: {pack_id}{Colors.ENDC}")
        return pack_id
    elif response and response.status_code == 400: # Handle existing pack
         print(f"{Colors.WARNING}Pack '{name}' might already exist. Trying to fetch it.{Colors.ENDC}")
         list_response = make_request("GET", "/packs/")
         if list_response and list_response.status_code == 200:
             packs = list_response.json().get("packs", [])
             for p in packs:
                 if p['name'].lower() == name.lower():
                     print(f"{Colors.GREEN}Found existing pack with ID: {p['id']}{Colors.ENDC}")
                     return p['id']
             print(f"{Colors.FAIL}Could not find pack '{name}' after creation attempt failed.{Colors.ENDC}")
             return None
         else:
             print(f"{Colors.FAIL}Failed to list packs to find existing one.{Colors.ENDC}")
             return None
    else:
        print(f"{Colors.FAIL}Failed to create or find pack '{name}'. Status: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return None


def add_topic(pack_id: str, custom_topic: str) -> bool:
    """Add a specific topic to a pack."""
    # Skip the initialization step and directly set our custom topic
    data = {
        "predefined_topic": custom_topic
    }

    print_step(f"Adding custom topic '{custom_topic}' to pack ID: {pack_id}")

    # Use the regular topics endpoint with predefined_topic to set just this topic
    response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)

    if response and response.status_code == 200:
        result = response.json()
        topics = result.get("topics", [])
        print(f"{Colors.GREEN}Successfully added topic. All topics:{Colors.ENDC}")
        for i, topic in enumerate(topics, 1):
            print(f"  {i}. {topic}")
        # Verify the specific topic was added
        if custom_topic in topics:
            return True
        else:
             print(f"{Colors.WARNING}Custom topic '{custom_topic}' not found in response topics list.{Colors.ENDC}")
             return False
    else:
        print(f"{Colors.FAIL}Failed to add custom topic: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return False

def generate_difficulties(pack_id: str) -> bool:
    """Generate difficulty descriptions for a pack."""
    data = {
        "force_regenerate": False # Don't force regenerate unless needed
    }

    print_step(f"Generating/Ensuring difficulty descriptions for pack ID: {pack_id}")
    response = make_request("POST", f"/packs/{pack_id}/difficulties/", json_data=data)

    if response and response.status_code == 200:
        print(f"{Colors.GREEN}Successfully generated/ensured difficulty descriptions{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}Failed to generate difficulties: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return False

def process_seed_questions(pack_id: str, seed_questions_file: Optional[str]) -> Dict[str, str]:
    """Process seed questions from a file."""
    if not seed_questions_file:
        print(f"{Colors.CYAN}No seed questions file provided, skipping.{Colors.ENDC}")
        return {}

    if not os.path.exists(seed_questions_file):
        print(f"{Colors.FAIL}Seed questions file not found: {seed_questions_file}{Colors.ENDC}")
        return {}

    print_step(f"Processing seed questions from {seed_questions_file}")
    try:
        with open(seed_questions_file, 'r') as f:
            seed_content = f.read()

        # Use extraction API
        data = {"text_content": seed_content}
        print(f"{Colors.CYAN}Extracting seed questions using LLM for pack ID: {pack_id}{Colors.ENDC}")
        response = make_request("POST", f"/packs/{pack_id}/questions/seed/extract", json_data=data)

        if response and response.status_code == 200:
            result = response.json()
            seed_questions = result.get("seed_questions", {})
            count = result.get("count", 0)
            print(f"{Colors.GREEN}Successfully extracted and stored {count} seed questions{Colors.ENDC}")
            return seed_questions
        else:
            print(f"{Colors.FAIL}Failed to extract seed questions: {response.status_code if response else 'N/A'}{Colors.ENDC}")
            return {}
    except Exception as e:
        print(f"{Colors.FAIL}Error processing seed questions file: {str(e)}{Colors.ENDC}")
        print(traceback.format_exc())
        return {}

def generate_custom_instructions(pack_id: str, topic: str) -> Optional[str]:
    """Generate custom instructions for a specific topic using the LLM."""
    data = {"pack_topic": topic}

    print_step(f"Auto-generating custom instructions for topic '{topic}'")
    response = make_request("POST", f"/packs/{pack_id}/questions/custom-instructions/generate", json_data=data)

    if response and response.status_code == 200:
        result = response.json()
        custom_instructions = result.get("custom_instructions")
        if custom_instructions:
             print(f"{Colors.GREEN}Successfully generated custom instructions:{Colors.ENDC}")
             print(f"{Colors.CYAN}{custom_instructions}{Colors.ENDC}")
        else:
             print(f"{Colors.WARNING}API returned success but no custom instructions content.{Colors.ENDC}")
        return custom_instructions
    else:
        print(f"{Colors.FAIL}Failed to auto-generate custom instructions: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return None

# Removed load_custom_instructions as the file input is removed

def generate_questions(
    pack_id: str,
    topic: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    custom_instructions: Optional[str] = None, # Still accept manual override if needed, but test focuses on auto/none
    debug_mode: bool = False
) -> List[Dict[str, Any]]:
    """Generate questions for a pack. Uses fetched/provided custom instructions."""
    # Prepare request data
    data = {
        "pack_topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "debug_mode": debug_mode
        # Custom instructions are now handled internally by the service
        # based on the topic, but we can still pass an override here if needed.
        # If `custom_instructions` is passed, it acts as an override for this specific call.
        # "custom_instructions": custom_instructions # <-- This is now less common for the test
    }

    print_step(f"Generating {num_questions} questions for topic '{topic}' with difficulty '{difficulty}'")

    response = make_request("POST", f"/packs/{pack_id}/questions/", json_data=data)

    if response and response.status_code == 200:
        result = response.json()
        questions = result.get("questions", [])
        print(f"{Colors.GREEN}Successfully generated {len(questions)} questions{Colors.ENDC}")
        # Note: The response from this endpoint now includes generated incorrect answers too
        return questions
    else:
        print(f"{Colors.FAIL}Failed to generate questions: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return []

def display_questions(questions: List[Dict[str, Any]]) -> None:
    """Display questions with answers and metadata."""
    if not questions:
        print(f"{Colors.WARNING}No questions to display{Colors.ENDC}")
        return

    print(f"\n{Colors.HEADER}Generated Questions:{Colors.ENDC}")
    for i, q in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}:{Colors.ENDC}")
        print(f"  ID: {q.get('id', 'N/A')}")
        print(f"  {Colors.BLUE}Q: {q['question']}{Colors.ENDC}")
        print(f"  {Colors.GREEN}A: {q['answer']}{Colors.ENDC}")

        # Display additional metadata
        print(f"  {Colors.CYAN}Topic: {q.get('pack_topics_item', 'N/A')}{Colors.ENDC}")
        print(f"  {Colors.CYAN}Difficulty: {q.get('difficulty_current', 'N/A')}{Colors.ENDC}")
        # Incorrect answers are generated by the endpoint now, but not typically part of the response model here.
        # If you need to verify them, you'd need another API call or modify the response model.

def save_to_file(content: str, filename: str) -> bool:
    """Save content to a file."""
    try:
        with open(filename, 'w') as f:
            f.write(content)
        print(f"{Colors.GREEN}Successfully saved to {filename}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.FAIL}Error saving to file: {str(e)}{Colors.ENDC}")
        return False

def run_generator(args: argparse.Namespace) -> None:
    """Run the full question generation pipeline."""
    # Create the pack
    pack_id = create_pack(args.pack_name)
    if not pack_id: return

    # Add the custom topic
    if not add_topic(pack_id, args.topic):
        print(f"{Colors.FAIL}Stopping test: Failed to add custom topic.{Colors.ENDC}")
        return

    # Generate difficulty descriptions
    generate_difficulties(pack_id) # Continue even if this fails

    # Process seed questions if provided
    seed_questions = process_seed_questions(pack_id, args.seed_questions)

    # Handle custom instructions
    custom_instructions = None
    if args.auto_generate_instructions:
        # Auto-generate instructions for the specified topic
        custom_instructions = generate_custom_instructions(pack_id, args.topic)

        # Save generated instructions if requested
        if custom_instructions and args.save_generated_instructions:
            save_to_file(custom_instructions, args.save_generated_instructions)
    # Removed handling for --custom-instructions file, as it's less relevant now

    # Generate questions with the custom topic
    # The service will internally fetch the stored custom instructions for the topic
    questions = generate_questions(
        pack_id=pack_id,
        topic=args.topic,
        difficulty=args.difficulty,
        num_questions=args.num_questions,
        # custom_instructions=custom_instructions, # Don't pass here unless overriding internal fetch
        debug_mode=args.debug
    )

    # Display the generated questions
    display_questions(questions)

    # Print summary
    print(f"\n{Colors.HEADER}Summary:{Colors.ENDC}")
    print(f"  Pack ID: {pack_id}")
    print(f"  Pack Name: {args.pack_name}")
    print(f"  Topic Tested: {args.topic}")
    print(f"  Seed Questions Used: {'Yes' if seed_questions else 'No'} ({len(seed_questions)})")
    print(f"  Auto-Generated Instructions: {'Yes' if args.auto_generate_instructions else 'No'}")
    print(f"    Generated/Used Instructions: {'Yes' if custom_instructions else 'No'}")
    if args.save_generated_instructions and custom_instructions:
        print(f"    Saved To: {args.save_generated_instructions}")
    print(f"  Difficulty: {args.difficulty}")
    print(f"  Questions Generated: {len(questions)}")
    print(f"\n{Colors.CYAN}You can use this pack ID for future testing: {pack_id}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Test Trivia Question Generation API with per-topic instructions")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack")
    parser.add_argument("--topic", "-t", required=True, help="Custom topic to use for questions")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions (used for instruction generation)")
    # REMOVED --custom-instructions file argument
    parser.add_argument("--auto-generate-instructions", "-a", action="store_true",
                        help="Auto-generate custom instructions for the specified topic using LLM")
    parser.add_argument("--save-generated-instructions", "-g",
                        help="Save the auto-generated instructions to this file")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard", "expert", "mixed"],
                      default="mixed", help="Difficulty level for questions")
    parser.add_argument("--num-questions", "-n", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for API calls")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode in the API request payload")

    # Access args globally for make_request logging
    global args
    args = parser.parse_args()

    run_generator(args)

if __name__ == "__main__":
    main()