import requests
import json
import sys
import argparse
from typing import Dict, List, Any, Optional
import uuid

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

def get_topics(pack_id: str) -> List[str]:
    """Get topics for a pack."""
    response = requests.get(f"{BASE_URL}/packs/{pack_id}/topics/")
    if response.status_code == 200:
        return response.json().get("topics", [])
    else:
        print(f"{Colors.FAIL}Failed to get topics: {response.status_code}{Colors.ENDC}")
        return []

def get_difficulties(pack_id: str) -> Dict[str, Dict[str, str]]:
    """Get difficulty descriptions for a pack."""
    response = requests.get(f"{BASE_URL}/packs/{pack_id}/difficulties/")
    if response.status_code == 200:
        return response.json().get("descriptions", {})
    else:
        print(f"{Colors.FAIL}Failed to get difficulties: {response.status_code}{Colors.ENDC}")
        return {}

def generate_questions(pack_id: str, topic: str, difficulty: str, num_questions: int = 3, debug_mode: bool = False) -> List[Dict[str, Any]]:
    """Generate questions for a pack with a specific topic and difficulty."""
    data = {
        "pack_topic": topic,
        "difficulty": difficulty.lower(),
        "num_questions": num_questions,
        "debug_mode": debug_mode
    }
    
    print(f"\n{Colors.BOLD}Generating {num_questions} questions for topic '{topic}' at {difficulty} difficulty{Colors.ENDC}")
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
    """Display questions and answers."""
    for i, q in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}Question {i}:{Colors.ENDC}")
        print(f"{Colors.BLUE}Q: {q['question']}{Colors.ENDC}")
        print(f"{Colors.GREEN}A: {q['answer']}{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Test question generation for a trivia pack")
    parser.add_argument("pack_id", help="ID of the pack to generate questions for")
    parser.add_argument("--topic", help="Specific topic to use")
    parser.add_argument("--difficulty", default="medium", choices=["easy", "medium", "hard", "expert"], 
                        help="Difficulty level for questions")
    parser.add_argument("--num", "-n", type=int, default=3, help="Number of questions to generate")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    parser.add_argument("--list-topics", "-lt", action="store_true", help="List available topics")
    args = parser.parse_args()
    
    # List topics if requested
    if args.list_topics:
        topics = get_topics(args.pack_id)
        if topics:
            print(f"\n{Colors.BOLD}Available topics for pack {args.pack_id}:{Colors.ENDC}")
            for i, topic in enumerate(topics, 1):
                print(f"{i}. {topic}")
        else:
            print(f"{Colors.WARNING}No topics found for pack {args.pack_id}{Colors.ENDC}")
        return
    
    # Determine the topic to use
    topic = args.topic
    if not topic:
        topics = get_topics(args.pack_id)
        if not topics:
            print(f"{Colors.FAIL}No topics found for pack {args.pack_id}. Cannot generate questions.{Colors.ENDC}")
            return
        
        # Let user select a topic
        print(f"\n{Colors.BOLD}Available topics:{Colors.ENDC}")
        for i, t in enumerate(topics, 1):
            print(f"{i}. {t}")
        
        try:
            choice = int(input("\nSelect a topic (number): ")) - 1
            if choice < 0 or choice >= len(topics):
                print(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")
                return
            topic = topics[choice]
        except (ValueError, IndexError):
            print(f"{Colors.FAIL}Invalid input.{Colors.ENDC}")
            return
    
    # Generate and display questions
    questions = generate_questions(
        pack_id=args.pack_id,
        topic=topic,
        difficulty=args.difficulty,
        num_questions=args.num,
        debug_mode=args.debug
    )
    
    if questions:
        display_questions(questions)

if __name__ == "__main__":
    main()