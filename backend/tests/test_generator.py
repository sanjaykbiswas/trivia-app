# python3 tests/test_generator.py --pack-name "Book Title Adjectives" --topic "Book Title Adjectives" --seed-questions seed_questions.txt -a -g generated_instruction.txt -v
# python3 tests/test_generator.py --pack-name "Physics Concepts" --topic "Quantum Mechanics" -n 10 -d hard -a

#!/usr/bin/env python
import requests
import json
import argparse
import sys
from typing import Dict, List, Any, Optional
import os
import traceback
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
    elif response and response.status_code == 400:
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
    data = { "predefined_topic": custom_topic }
    print_step(f"Adding custom topic '{custom_topic}' to pack ID: {pack_id}")
    response = make_request("POST", f"/packs/{pack_id}/topics/", json_data=data)

    if response and response.status_code == 200:
        result = response.json()
        topics = result.get("topics", [])
        print(f"{Colors.GREEN}Successfully added topic. All topics:{Colors.ENDC}")
        for i, topic in enumerate(topics, 1): print(f"  {i}. {topic}")
        if custom_topic in topics: return True
        else: print(f"{Colors.WARNING}Custom topic '{custom_topic}' not found in response topics list.{Colors.ENDC}"); return False
    else:
        print(f"{Colors.FAIL}Failed to add custom topic: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return False

def generate_difficulties(pack_id: str) -> bool:
    """Generate difficulty descriptions for a pack."""
    data = { "force_regenerate": False }
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

    # --- MODIFIED: Correct path construction ---
    script_dir = Path(__file__).parent
    absolute_seed_path = script_dir.parent / seed_questions_file # Assumes seed file is in backend/
    if not absolute_seed_path.exists():
        print(f"{Colors.FAIL}Seed questions file not found at expected location: {absolute_seed_path}{Colors.ENDC}")
        return {}
    # --- END MODIFIED ---

    print_step(f"Processing seed questions from {absolute_seed_path}")
    try:
        with open(absolute_seed_path, 'r') as f:
            seed_content = f.read()

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

def generate_questions(
    pack_id: str,
    topic: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    debug_mode: bool = False
) -> List[Dict[str, Any]]:
    """Generate questions for a pack. Service handles instruction fetching."""
    data = {
        "pack_topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "debug_mode": debug_mode
    }
    print_step(f"Generating {num_questions} questions for topic '{topic}' with difficulty '{difficulty}'")
    response = make_request("POST", f"/packs/{pack_id}/questions/", json_data=data)

    if response and response.status_code == 200:
        result = response.json()
        questions = result.get("questions", [])
        print(f"{Colors.GREEN}Successfully generated {len(questions)} questions{Colors.ENDC}")
        return questions
    else:
        print(f"{Colors.FAIL}Failed to generate questions: {response.status_code if response else 'N/A'}{Colors.ENDC}")
        return []

def display_questions(questions: List[Dict[str, Any]]) -> None:
    """Display questions with answers and metadata."""
    if not questions: print(f"{Colors.WARNING}No questions to display{Colors.ENDC}"); return
    print(f"\n{Colors.HEADER}Generated Questions:{Colors.ENDC}")
    for i, q in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}:{Colors.ENDC}")
        print(f"  ID: {q.get('id', 'N/A')}")
        print(f"  {Colors.BLUE}Q: {q['question']}{Colors.ENDC}")
        print(f"  {Colors.GREEN}A: {q['answer']}{Colors.ENDC}")
        print(f"  {Colors.CYAN}Topic: {q.get('pack_topics_item', 'N/A')}{Colors.ENDC}")
        print(f"  {Colors.CYAN}Difficulty: {q.get('difficulty_current', 'N/A')}{Colors.ENDC}")

def save_to_file(content: str, filename: str) -> bool:
    """Save content to a file."""
    try:
        # --- MODIFIED: Save relative to script's parent (backend/) ---
        script_dir = Path(__file__).parent
        absolute_save_path = script_dir.parent / filename
        with open(absolute_save_path, 'w') as f:
            f.write(content)
        print(f"{Colors.GREEN}Successfully saved to {absolute_save_path}{Colors.ENDC}")
        # --- END MODIFIED ---
        return True
    except Exception as e:
        print(f"{Colors.FAIL}Error saving to file: {str(e)}{Colors.ENDC}")
        return False

def run_generator(args: argparse.Namespace) -> None:
    """Run the full question generation pipeline."""
    pack_id = create_pack(args.pack_name)
    if not pack_id: return
    if not add_topic(pack_id, args.topic): print(f"{Colors.FAIL}Stopping test: Failed to add custom topic.{Colors.ENDC}"); return
    generate_difficulties(pack_id)
    seed_questions = process_seed_questions(pack_id, args.seed_questions)

    custom_instructions = None
    if args.auto_generate_instructions:
        custom_instructions = generate_custom_instructions(pack_id, args.topic)
        if custom_instructions and args.save_generated_instructions:
            save_to_file(custom_instructions, args.save_generated_instructions)

    questions = generate_questions( pack_id=pack_id, topic=args.topic, difficulty=args.difficulty, num_questions=args.num_questions, debug_mode=args.debug )
    display_questions(questions)

    print(f"\n{Colors.HEADER}Summary:{Colors.ENDC}")
    print(f"  Pack ID: {pack_id}")
    print(f"  Pack Name: {args.pack_name}")
    print(f"  Topic Tested: {args.topic}")
    print(f"  Seed Questions Used: {'Yes' if seed_questions else 'No'} ({len(seed_questions)})")
    print(f"  Auto-Generated Instructions: {'Yes' if args.auto_generate_instructions else 'No'}")
    print(f"    Generated/Used Instructions: {'Yes' if custom_instructions else 'No'}")
    if args.save_generated_instructions and custom_instructions: print(f"    Saved To: {args.save_generated_instructions}")
    print(f"  Difficulty: {args.difficulty}")
    print(f"  Questions Generated: {len(questions)}")
    print(f"\n{Colors.CYAN}You can use this pack ID for future testing: {pack_id}{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Test Trivia Question Generation API with per-topic instructions")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack")
    parser.add_argument("--topic", "-t", required=True, help="Custom topic to use for questions")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions (relative to backend/)")
    parser.add_argument("--auto-generate-instructions", "-a", action="store_true", help="Auto-generate custom instructions for the specified topic using LLM")
    parser.add_argument("--save-generated-instructions", "-g", help="Save the auto-generated instructions to this file (relative to backend/)")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard", "expert", "mixed"], default="mixed", help="Difficulty level for questions")
    parser.add_argument("--num-questions", "-n", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for API calls")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode in the API request payload")

    global args
    args = parser.parse_args()

    run_generator(args)

if __name__ == "__main__":
    main()