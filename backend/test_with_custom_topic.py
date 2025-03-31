#!/usr/bin/env python
import requests
import json
import argparse
import sys
import uuid
from typing import Dict, List, Any, Optional

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
    print(json.dumps(data, indent=2))

def create_pack(name: str, description: str = None) -> Optional[str]:
    """Create a new pack and return its ID."""
    data = {
        "name": name,
        "description": description or f"Custom pack created with specific topic",
        "price": 0.0,
        "creator_type": "system"
    }
    
    print(f"{Colors.HEADER}Creating pack: {name}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/", json=data)
    
    if response.status_code == 201:
        pack_data = response.json()
        pack_id = pack_data.get("id")
        print(f"{Colors.GREEN}Successfully created pack with ID: {pack_id}{Colors.ENDC}")
        return pack_id
    else:
        print(f"{Colors.FAIL}Failed to create pack: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def store_custom_topic(pack_id: str, custom_topic: str) -> bool:
    """Store a custom topic for a pack."""
    # For this function, we'll use the topics endpoint but just send our single custom topic
    data = {
        "num_topics": 1,  # This is required but won't be used since we're providing our topic directly
        "creation_name": None  # Let the backend use the pack name
    }
    
    print(f"{Colors.HEADER}Storing custom topic for pack ID: {pack_id}{Colors.ENDC}")
    print(f"{Colors.CYAN}Topic: {custom_topic}{Colors.ENDC}")
    
    # First post to create topic structure
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/topics/", json=data)
    
    if response.status_code != 200:
        print(f"{Colors.FAIL}Failed to initialize topics: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return False
    
    # Now use the additional topics endpoint to replace with our custom topic
    additional_data = {
        "num_additional_topics": 1  # We're adding just one topic
    }
    
    # This is a bit of a hack since we don't have a direct "set topic" endpoint
    # We'll first get current topics, then use the additional endpoint to add our custom one
    response = requests.get(f"{BASE_URL}/packs/{pack_id}/topics/")
    
    if response.status_code == 200:
        # We've successfully posted a topic, now use the text extraction to add our custom topic
        topics_data = response.json()
        existing_topics = topics_data.get("topics", [])
        print(f"Initial topics created: {', '.join(existing_topics)}")
        
        # Now add our custom topic
        add_response = requests.post(f"{BASE_URL}/packs/{pack_id}/topics/additional", json=additional_data)
        
        if add_response.status_code == 200:
            added_data = add_response.json()
            all_topics = added_data.get("topics", [])
            print(f"{Colors.GREEN}Successfully added custom topic. All topics:{Colors.ENDC}")
            for i, topic in enumerate(all_topics, 1):
                print(f"{i}. {topic}")
                
            # Our custom topic should be the last one in the list
            return custom_topic in all_topics
        else:
            print(f"{Colors.FAIL}Failed to add custom topic: {add_response.status_code}{Colors.ENDC}")
            return False
    else:
        print(f"{Colors.FAIL}Failed to get topics: {response.status_code}{Colors.ENDC}")
        return False

def generate_difficulties(pack_id: str) -> bool:
    """Generate difficulty descriptions for a pack."""
    data = {
        "force_regenerate": True
    }
    
    print(f"{Colors.HEADER}Generating difficulty descriptions for pack ID: {pack_id}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/difficulties/", json=data)
    
    if response.status_code == 200:
        print(f"{Colors.GREEN}Successfully generated difficulty descriptions{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}Failed to generate difficulties: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return False

def extract_or_store_seed_questions(pack_id: str, seed_questions_file: str) -> Dict[str, str]:
    """Process seed questions from a file."""
    if not seed_questions_file:
        print(f"{Colors.WARNING}No seed questions file provided, skipping.{Colors.ENDC}")
        return {}
        
    try:
        with open(seed_questions_file, 'r') as f:
            seed_content = f.read()
            
        # Try to parse as JSON first
        try:
            seed_questions = json.loads(seed_content)
            if isinstance(seed_questions, dict):
                # It's already in the expected format
                if store_seed_questions(pack_id, seed_questions):
                    return seed_questions
                return {}
            else:
                print(f"{Colors.WARNING}Seed questions file is not a valid JSON object, using LLM extraction{Colors.ENDC}")
        except json.JSONDecodeError:
            # Not JSON, use LLM to extract
            pass
        
        # Use extraction API
        return extract_seed_questions(pack_id, seed_content)
    except Exception as e:
        print(f"{Colors.FAIL}Error processing seed questions file: {str(e)}{Colors.ENDC}")
        return {}

def extract_seed_questions(pack_id: str, text_content: str) -> Dict[str, str]:
    """Extract seed questions from text using the LLM processor."""
    data = {
        "text_content": text_content
    }
    
    print(f"{Colors.HEADER}Extracting seed questions using LLM for pack ID: {pack_id}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/seed/extract", json=data)
    
    if response.status_code == 200:
        result = response.json()
        seed_questions = result.get("seed_questions", {})
        count = result.get("count", 0)
        print(f"{Colors.GREEN}Successfully extracted {count} seed questions{Colors.ENDC}")
        return seed_questions
    else:
        print(f"{Colors.FAIL}Failed to extract seed questions: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return {}

def store_seed_questions(pack_id: str, seed_questions: Dict[str, str]) -> bool:
    """Store seed questions for a pack."""
    if not seed_questions:
        print(f"{Colors.WARNING}No seed questions to store{Colors.ENDC}")
        return True
        
    data = {
        "seed_questions": seed_questions
    }
    
    print(f"{Colors.HEADER}Storing {len(seed_questions)} seed questions for pack ID: {pack_id}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/seed", json=data)
    
    if response.status_code == 200:
        print(f"{Colors.GREEN}Successfully stored seed questions{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.FAIL}Failed to store seed questions: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return False

def generate_questions(
    pack_id: str, 
    topic: str, 
    difficulty: str = "mixed", 
    num_questions: int = 5,
    custom_instructions: str = None,
    debug_mode: bool = False
) -> List[Dict[str, Any]]:
    """Generate questions for a pack with custom instructions."""
    data = {
        "pack_topic": topic,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "debug_mode": debug_mode
    }
    
    if custom_instructions:
        data["custom_instructions"] = custom_instructions
    
    print(f"{Colors.HEADER}Generating {num_questions} questions for topic '{topic}' "
          f"with difficulty '{difficulty}'{Colors.ENDC}")
    if custom_instructions:
        print(f"{Colors.CYAN}Using custom instructions:{Colors.ENDC}\n{custom_instructions}")
    
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        questions = result.get("questions", [])
        print(f"{Colors.GREEN}Successfully generated {len(questions)} questions{Colors.ENDC}")
        return questions
    else:
        print(f"{Colors.FAIL}Failed to generate questions: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return []

def display_questions(questions: List[Dict[str, Any]]) -> None:
    """Display questions with answers and metadata."""
    if not questions:
        print(f"{Colors.WARNING}No questions to display{Colors.ENDC}")
        return
    
    print(f"\n{Colors.HEADER}Generated Questions:{Colors.ENDC}")
    for i, q in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}:{Colors.ENDC}")
        print(f"{Colors.BLUE}Q: {q['question']}{Colors.ENDC}")
        print(f"{Colors.GREEN}A: {q['answer']}{Colors.ENDC}")
        
        # Display additional metadata
        print(f"{Colors.CYAN}Topic: {q.get('pack_topics_item', 'N/A')}{Colors.ENDC}")
        print(f"{Colors.CYAN}Difficulty: {q.get('difficulty_current', 'N/A')}{Colors.ENDC}")

def test_with_custom_topic(
    pack_name: str,
    custom_topic: str,
    seed_questions_file: str = None,
    custom_instructions_file: str = None,
    difficulty: str = "mixed",
    num_questions: int = 5,
    debug_mode: bool = False
) -> None:
    """
    Test generating questions with a custom topic, seed questions and custom instructions.
    
    Args:
        pack_name: Name for the pack
        custom_topic: The specific topic to use for question generation
        seed_questions_file: Optional path to a file containing seed questions
        custom_instructions_file: Optional path to a file with custom instructions
        difficulty: Difficulty level for questions (easy, medium, hard, expert, mixed)
        num_questions: Number of questions to generate
        debug_mode: Enable debug mode for more detailed output
    """
    # Create the pack
    pack_id = create_pack(pack_name)
    if not pack_id:
        return
    
    # Store our custom topic
    if not store_custom_topic(pack_id, custom_topic):
        print(f"{Colors.WARNING}Failed to store custom topic, but continuing with test{Colors.ENDC}")
    
    # Generate difficulties
    if not generate_difficulties(pack_id):
        print(f"{Colors.WARNING}Failed to generate difficulties, but continuing with test{Colors.ENDC}")
    
    # Process seed questions if provided
    seed_questions = {}
    if seed_questions_file:
        seed_questions = extract_or_store_seed_questions(pack_id, seed_questions_file)
    
    # Load custom instructions if provided
    custom_instructions = None
    if custom_instructions_file:
        try:
            with open(custom_instructions_file, 'r') as f:
                custom_instructions = f.read()
        except Exception as e:
            print(f"{Colors.FAIL}Error reading custom instructions file: {str(e)}{Colors.ENDC}")
    
    # Generate questions with our custom topic
    questions = generate_questions(
        pack_id=pack_id,
        topic=custom_topic,
        difficulty=difficulty,
        num_questions=num_questions,
        custom_instructions=custom_instructions,
        debug_mode=debug_mode
    )
    
    # Display the generated questions
    display_questions(questions)
    
    # Print summary
    print(f"\n{Colors.HEADER}Summary:{Colors.ENDC}")
    print(f"Pack ID: {pack_id}")
    print(f"Pack Name: {pack_name}")
    print(f"Custom Topic: {custom_topic}")
    print(f"Difficulty: {difficulty}")
    print(f"Seed Questions: {len(seed_questions)}")
    print(f"Custom Instructions: {'Yes' if custom_instructions else 'No'}")
    print(f"Generated Questions: {len(questions)}")
    print(f"\nYou can access this pack via the API using the pack ID above.")

def main():
    parser = argparse.ArgumentParser(description="Test question generation with custom topic, seed questions, and instructions")
    parser.add_argument("pack_name", help="Name for the trivia pack")
    parser.add_argument("custom_topic", help="Custom topic to use for question generation")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions")
    parser.add_argument("--custom-instructions", "-i", help="Path to a file containing custom instructions")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard", "expert", "mixed"], 
                        default="mixed", help="Difficulty level for questions (default: mixed)")
    parser.add_argument("--num-questions", "-n", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for question generation")
    
    args = parser.parse_args()
    
    test_with_custom_topic(
        pack_name=args.pack_name,
        custom_topic=args.custom_topic,
        seed_questions_file=args.seed_questions,
        custom_instructions_file=args.custom_instructions,
        difficulty=args.difficulty,
        num_questions=args.num_questions,
        debug_mode=args.debug
    )

if __name__ == "__main__":
    main()