# python3 test_generator.py --pack-name "Book Title Adjectives" --topic "Book Title Adjectives" --seed-questions seed_questions.txt --auto-generate-instructions

#!/usr/bin/env python
import requests
import json
import argparse
import sys
from typing import Dict, List, Any, Optional
import os

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
        "description": description or f"Custom pack created for testing",
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

def add_topic(pack_id: str, custom_topic: str) -> bool:
    """Add a specific topic to a pack."""
    # Skip the initialization step and directly set our custom topic
    data = {
        "predefined_topic": custom_topic
    }
    
    print(f"{Colors.HEADER}Adding custom topic '{custom_topic}' to pack ID: {pack_id}{Colors.ENDC}")
    
    # Use the regular topics endpoint with predefined_topic to set just this topic
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/topics/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        topics = result.get("topics", [])
        print(f"{Colors.GREEN}Successfully added topic. All topics:{Colors.ENDC}")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic}")
        return custom_topic in topics
    else:
        print(f"{Colors.FAIL}Failed to add custom topic: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
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

def process_seed_questions(pack_id: str, seed_questions_file: str) -> Dict[str, str]:
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
                data = {"seed_questions": seed_questions}
                print(f"{Colors.HEADER}Storing {len(seed_questions)} seed questions for pack ID: {pack_id}{Colors.ENDC}")
                response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/seed", json=data)
                
                if response.status_code == 200:
                    print(f"{Colors.GREEN}Successfully stored seed questions{Colors.ENDC}")
                    return seed_questions
                else:
                    print(f"{Colors.FAIL}Failed to store seed questions: {response.status_code}{Colors.ENDC}")
                    return {}
            else:
                print(f"{Colors.WARNING}Seed questions file is not a valid JSON object, using LLM extraction{Colors.ENDC}")
        except json.JSONDecodeError:
            # Not JSON, use LLM to extract
            pass
        
        # Use extraction API
        data = {"text_content": seed_content}
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
    except Exception as e:
        print(f"{Colors.FAIL}Error processing seed questions file: {str(e)}{Colors.ENDC}")
        return {}

def generate_custom_instructions(pack_id: str, topic: str) -> Optional[str]:
    """Generate custom instructions for question generation using the LLM."""
    data = {
        "pack_topic": topic
    }
    
    print(f"{Colors.HEADER}Generating custom instructions for topic '{topic}'{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/custom-instructions/generate", json=data)
    
    if response.status_code == 200:
        result = response.json()
        custom_instructions = result.get("custom_instructions")
        print(f"{Colors.GREEN}Successfully generated custom instructions:{Colors.ENDC}")
        print(f"{Colors.CYAN}{custom_instructions}{Colors.ENDC}")
        return custom_instructions
    else:
        print(f"{Colors.FAIL}Failed to generate custom instructions: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def load_custom_instructions(custom_instructions_file: str) -> Optional[str]:
    """Load custom instructions from a file."""
    if not custom_instructions_file:
        return None
        
    try:
        with open(custom_instructions_file, 'r') as f:
            custom_instructions = f.read()
        print(f"{Colors.CYAN}Using custom instructions from file:{Colors.ENDC}\n{custom_instructions}")
        return custom_instructions
    except Exception as e:
        print(f"{Colors.FAIL}Error reading custom instructions file: {str(e)}{Colors.ENDC}")
        return None

def generate_questions(
    pack_id: str, 
    topic: str, 
    difficulty: str = "medium", 
    num_questions: int = 5,
    custom_instructions: Optional[str] = None,
    debug_mode: bool = False
) -> List[Dict[str, Any]]:
    """Generate questions for a pack with custom instructions."""
    # Prepare request data
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

def run_generator(
    pack_name: str,
    custom_topic: str,
    seed_questions_file: str = None,
    custom_instructions_file: str = None,
    auto_generate_instructions: bool = False,
    save_generated_instructions: Optional[str] = None,
    difficulty: str = "medium",
    num_questions: int = 5,
    debug_mode: bool = False
) -> None:
    """Run the full question generation pipeline."""
    # Create the pack
    pack_id = create_pack(pack_name)
    if not pack_id:
        return
    
    # Add the custom topic
    if not add_topic(pack_id, custom_topic):
        print(f"{Colors.WARNING}Failed to add custom topic, but continuing...{Colors.ENDC}")
        return
    
    # Generate difficulty descriptions
    if not generate_difficulties(pack_id):
        print(f"{Colors.WARNING}Failed to generate difficulties, but continuing...{Colors.ENDC}")
    
    # Process seed questions if provided
    seed_questions = {}
    if seed_questions_file:
        seed_questions = process_seed_questions(pack_id, seed_questions_file)
    
    # Handle custom instructions: generate or load from file
    custom_instructions = None
    
    if auto_generate_instructions:
        print(f"{Colors.HEADER}Auto-generating custom instructions based on seed questions{Colors.ENDC}")
        custom_instructions = generate_custom_instructions(pack_id, custom_topic)
        
        # Save generated instructions if requested
        if custom_instructions and save_generated_instructions:
            save_to_file(custom_instructions, save_generated_instructions)
    elif custom_instructions_file:
        custom_instructions = load_custom_instructions(custom_instructions_file)
    
    # Generate questions with the custom topic
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
    print(f"Seed Questions: {len(seed_questions)}")
    print(f"Used Custom Instructions: {'Yes' if custom_instructions else 'No'}")
    print(f"Generated Questions: {len(questions)}")
    print(f"\nYou can use this pack ID for future testing: {pack_id}")

def main():
    parser = argparse.ArgumentParser(description="Generate trivia questions with custom topic and options")
    parser.add_argument("--pack-name", "-p", required=True, help="Name for the trivia pack")
    parser.add_argument("--topic", "-t", required=True, help="Custom topic to use for questions")
    parser.add_argument("--seed-questions", "-s", help="Path to a file containing seed questions")
    parser.add_argument("--custom-instructions", "-i", help="Path to a file containing custom instructions")
    parser.add_argument("--auto-generate-instructions", "-a", action="store_true", 
                        help="Auto-generate custom instructions from seed questions")
    parser.add_argument("--save-generated-instructions", "-g", 
                        help="Save auto-generated instructions to this file")
    parser.add_argument("--difficulty", "-d", choices=["easy", "medium", "hard", "expert", "mixed"], 
                      default="mixed", help="Difficulty level for questions")
    parser.add_argument("--num-questions", "-n", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for more detailed output")
    
    args = parser.parse_args()
    
    # Check for conflicts
    if args.custom_instructions and args.auto_generate_instructions:
        print(f"{Colors.WARNING}Both custom instructions file and auto-generate flag provided. "
              f"Auto-generation will take precedence.{Colors.ENDC}")
    
    # Check if files exist
    if args.seed_questions and not os.path.exists(args.seed_questions):
        print(f"{Colors.FAIL}Seed questions file not found: {args.seed_questions}{Colors.ENDC}")
        return
    
    if args.custom_instructions and not os.path.exists(args.custom_instructions) and not args.auto_generate_instructions:
        print(f"{Colors.FAIL}Custom instructions file not found: {args.custom_instructions}{Colors.ENDC}")
        return
    
    run_generator(
        pack_name=args.pack_name,
        custom_topic=args.topic,
        seed_questions_file=args.seed_questions,
        custom_instructions_file=args.custom_instructions,
        auto_generate_instructions=args.auto_generate_instructions,
        save_generated_instructions=args.save_generated_instructions,
        difficulty=args.difficulty,
        num_questions=args.num_questions,
        debug_mode=args.debug
    )

if __name__ == "__main__":
    main()