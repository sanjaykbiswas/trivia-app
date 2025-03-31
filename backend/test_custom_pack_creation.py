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

def generate_topics(pack_id: str, num_topics: int = 5) -> List[str]:
    """Generate topics for a pack."""
    data = {
        "num_topics": num_topics
    }
    
    print(f"{Colors.HEADER}Generating {num_topics} topics for pack ID: {pack_id}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/packs/{pack_id}/topics/", json=data)
    
    if response.status_code == 200:
        topics_data = response.json()
        topics = topics_data.get("topics", [])
        print(f"{Colors.GREEN}Successfully generated {len(topics)} topics:{Colors.ENDC}")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic}")
        return topics
    else:
        print(f"{Colors.FAIL}Failed to generate topics: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return []

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
    difficulty: str = "medium", 
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

def create_custom_pack(
    name: str = None,
    description: str = None,
    seed_questions_file: str = None,
    custom_instructions_file: str = None,
    num_topics: int = 5,
    topic: str = None,
    difficulty: str = "medium",
    num_questions: int = 5,
    debug_mode: bool = False
) -> None:
    """Create a custom pack with seed questions and custom instructions."""
    # Create a unique pack name if not provided
    if not name:
        name = f"Custom Pack {uuid.uuid4().hex[:8]}"
    
    # Create the pack
    pack_id = create_pack(name, description)
    if not pack_id:
        return
    
    # Generate topics
    topics = generate_topics(pack_id, num_topics)
    if not topics:
        return
    
    # Generate difficulties
    if not generate_difficulties(pack_id):
        return
    
    # Process seed questions if provided
    seed_questions = {}
    if seed_questions_file:
        try:
            with open(seed_questions_file, 'r') as f:
                seed_content = f.read()
                
            # Try to parse as JSON first
            try:
                seed_questions = json.loads(seed_content)
                if isinstance(seed_questions, dict):
                    # Store the pre-formatted JSON directly
                    if not store_seed_questions(pack_id, seed_questions):
                        return
                else:
                    print(f"{Colors.WARNING}Seed questions file is not a valid JSON object, using LLM extraction{Colors.ENDC}")
                    seed_questions = extract_seed_questions(pack_id, seed_content)
            except json.JSONDecodeError:
                # Not JSON, use LLM to extract
                seed_questions = extract_seed_questions(pack_id, seed_content)
                
        except Exception as e:
            print(f"{Colors.FAIL}Error reading seed questions file: {str(e)}{Colors.ENDC}")
    
    # Load custom instructions if provided
    custom_instructions = None
    if custom_instructions_file:
        try:
            with open(custom_instructions_file, 'r') as f:
                custom_instructions = f.read()
        except Exception as e:
            print(f"{Colors.FAIL}Error reading custom instructions file: {str(e)}{Colors.ENDC}")
    
    # Select topic to use for questions
    selected_topic = topic if topic else topics[0]
    
    # Generate questions
    questions = generate_questions(
        pack_id=pack_id,
        topic=selected_topic,
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
    print(f"Pack Name: {name}")
    print(f"Topics: {', '.join(topics)}")
    print(f"Seed Questions: {len(seed_questions)}")
    print(f"Generated Questions: {len(questions)}")
    print(f"\nYou can access this pack via the API using the pack ID above.")

def main():
    parser = argparse.ArgumentParser(description="Create a custom trivia pack with seed questions and custom instructions")
    parser.add_argument("--name", help="Name for the trivia pack")
    parser.add_argument("--description", help="Description for the trivia pack")
    parser.add_argument("--seed-questions", help="Path to a file containing seed questions (any format)")
    parser.add_argument("--custom-instructions", help="Path to a file containing custom instructions")
    parser.add_argument("--num-topics", type=int, default=5, help="Number of topics to generate")
    parser.add_argument("--topic", help="Specific topic to use for question generation")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "expert"], default="medium", 
                        help="Difficulty level for questions")
    parser.add_argument("--num-questions", type=int, default=5, help="Number of questions to generate")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode for question generation")
    parser.add_argument("--pack-id", help="Use an existing pack ID instead of creating a new one")
    parser.add_argument("--seed-text", help="Raw text to extract seed questions from")
    
    args = parser.parse_args()
    
    if args.pack_id:
        # Use existing pack for generating questions
        pack_id = args.pack_id
        
        # Get topics to select from if topic not specified
        if not args.topic:
            print(f"{Colors.HEADER}Getting topics for existing pack ID: {pack_id}{Colors.ENDC}")
            response = requests.get(f"{BASE_URL}/packs/{pack_id}/topics/")
            
            if response.status_code == 200:
                topics_data = response.json()
                topics = topics_data.get("topics", [])
                
                if topics:
                    print(f"{Colors.GREEN}Available topics:{Colors.ENDC}")
                    for i, topic in enumerate(topics, 1):
                        print(f"{i}. {topic}")
                    
                    try:
                        choice = int(input("\nSelect a topic (number): ")) - 1
                        if 0 <= choice < len(topics):
                            selected_topic = topics[choice]
                        else:
                            print(f"{Colors.FAIL}Invalid choice. Using first topic.{Colors.ENDC}")
                            selected_topic = topics[0]
                    except (ValueError, IndexError):
                        print(f"{Colors.FAIL}Invalid input. Using first topic.{Colors.ENDC}")
                        selected_topic = topics[0]
                else:
                    print(f"{Colors.WARNING}No topics found for this pack. Please specify a topic.{Colors.ENDC}")
                    return
            else:
                print(f"{Colors.FAIL}Failed to get topics: {response.status_code}{Colors.ENDC}")
                return
        else:
            selected_topic = args.topic
        
        # Process seed questions
        if args.seed_questions:
            try:
                with open(args.seed_questions, 'r') as f:
                    seed_content = f.read()
                
                # Try to parse as JSON first, or use LLM extraction
                try:
                    seed_questions = json.loads(seed_content)
                    if isinstance(seed_questions, dict):
                        if not store_seed_questions(pack_id, seed_questions):
                            print(f"{Colors.WARNING}Failed to store seed questions, continuing anyway{Colors.ENDC}")
                    else:
                        print(f"{Colors.WARNING}Seed questions file is not a valid JSON object, using LLM extraction{Colors.ENDC}")
                        extract_seed_questions(pack_id, seed_content)
                except json.JSONDecodeError:
                    # Not JSON, use LLM to extract
                    extract_seed_questions(pack_id, seed_content)
                    
            except Exception as e:
                print(f"{Colors.FAIL}Error reading seed questions file: {str(e)}{Colors.ENDC}")
        
        # Process direct seed text if provided
        if args.seed_text:
            extract_seed_questions(pack_id, args.seed_text)
            
        # Load custom instructions if provided
        custom_instructions = None
        if args.custom_instructions:
            try:
                with open(args.custom_instructions, 'r') as f:
                    custom_instructions = f.read()
            except Exception as e:
                print(f"{Colors.FAIL}Error reading custom instructions file: {str(e)}{Colors.ENDC}")
        
        # Generate questions
        questions = generate_questions(
            pack_id=pack_id,
            topic=selected_topic,
            difficulty=args.difficulty,
            num_questions=args.num_questions,
            custom_instructions=custom_instructions,
            debug_mode=args.debug
        )
        
        # Display the generated questions
        display_questions(questions)
        
    else:
        # Create a new pack with everything
        create_custom_pack(
            name=args.name,
            description=args.description,
            seed_questions_file=args.seed_questions,
            custom_instructions_file=args.custom_instructions,
            num_topics=args.num_topics,
            topic=args.topic,
            difficulty=args.difficulty,
            num_questions=args.num_questions,
            debug_mode=args.debug
        )

if __name__ == "__main__":
    main()