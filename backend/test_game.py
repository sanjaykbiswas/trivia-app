#!/usr/bin/env python
# python3 test_game.py --pack-name "World History" --questions 10

import requests
import json
import argparse
import sys
import time
import random
import string
from typing import Dict, List, Any, Optional, Tuple
import os
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

def generate_random_name(prefix: str = "Player") -> str:
    """Generate a random name for a player or session."""
    random_suffix = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
    return f"{prefix}_{random_suffix}"

def create_temporary_user(display_name: Optional[str] = None, is_temporary: bool = True) -> Optional[Dict[str, Any]]:
    """Create a temporary user for testing."""
    if not display_name:
        display_name = generate_random_name("User")
    
    data = {
        "displayname": display_name,
        "is_temporary": is_temporary
    }
    
    print(f"{Colors.HEADER}Creating temporary user: {display_name}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/users/", json=data)
    
    if response.status_code == 201:
        user_data = response.json()
        print(f"{Colors.GREEN}Successfully created user with ID: {user_data['id']}{Colors.ENDC}")
        return user_data
    else:
        print(f"{Colors.FAIL}Failed to create user: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def create_or_get_pack(pack_id: Optional[str] = None, pack_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new pack or get an existing one."""
    if pack_id:
        print(f"{Colors.HEADER}Getting existing pack with ID: {pack_id}{Colors.ENDC}")
        response = requests.get(f"{BASE_URL}/packs/{pack_id}")
        
        if response.status_code == 200:
            pack_data = response.json()
            print(f"{Colors.GREEN}Successfully retrieved pack: {pack_data['name']}{Colors.ENDC}")
            return pack_data
        else:
            print(f"{Colors.FAIL}Failed to get pack with ID {pack_id}: {response.status_code}{Colors.ENDC}")
            try:
                error_data = response.json()
                print_json(error_data)
            except:
                print(response.text)
            return None
    
    if pack_name:
        # Try to create a new pack
        data = {
            "name": pack_name,
            "description": f"Test pack created for game testing",
            "price": 0.0,
            "creator_type": "system"
        }
        
        print(f"{Colors.HEADER}Creating pack: {pack_name}{Colors.ENDC}")
        response = requests.post(f"{BASE_URL}/packs/", json=data)
        
        if response.status_code == 201:
            pack_data = response.json()
            print(f"{Colors.GREEN}Successfully created pack with ID: {pack_data['id']}{Colors.ENDC}")
            return pack_data
        else:
            print(f"{Colors.FAIL}Failed to create pack: {response.status_code}{Colors.ENDC}")
            try:
                error_data = response.json()
                print_json(error_data)
            except:
                print(response.text)
            return None
    
    print(f"{Colors.FAIL}Either pack_id or pack_name must be provided{Colors.ENDC}")
    return None

def generate_pack_content(pack_id: str, topic: Optional[str] = None) -> bool:
    """Generate topics, difficulty descriptions, and questions for a pack."""
    # First, add a topic
    if not topic:
        topic = "General Knowledge"
    
    print(f"{Colors.HEADER}Adding topic '{topic}' to pack...{Colors.ENDC}")
    topic_data = {
        "predefined_topic": topic
    }
    topic_response = requests.post(f"{BASE_URL}/packs/{pack_id}/topics/", json=topic_data)
    
    if topic_response.status_code != 200:
        print(f"{Colors.FAIL}Failed to add topic: {topic_response.status_code}{Colors.ENDC}")
        return False
    
    # Generate difficulty descriptions
    print(f"{Colors.HEADER}Generating difficulty descriptions...{Colors.ENDC}")
    difficulty_data = {
        "force_regenerate": True
    }
    difficulty_response = requests.post(f"{BASE_URL}/packs/{pack_id}/difficulties/", json=difficulty_data)
    
    if difficulty_response.status_code != 200:
        print(f"{Colors.FAIL}Failed to generate difficulties: {difficulty_response.status_code}{Colors.ENDC}")
        return False
    
    # Generate questions
    print(f"{Colors.HEADER}Generating questions for topic '{topic}'...{Colors.ENDC}")
    question_data = {
        "pack_topic": topic,
        "difficulty": "mixed",
        "num_questions": 10,
        "debug_mode": False
    }
    question_response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/", json=question_data)
    
    if question_response.status_code == 200:
        result = question_response.json()
        print(f"{Colors.GREEN}Successfully generated {result.get('total', 0)} questions{Colors.ENDC}")
        
        # Generate incorrect answers for all questions
        print(f"{Colors.HEADER}Generating incorrect answers...{Colors.ENDC}")
        incorrect_response = requests.post(f"{BASE_URL}/packs/{pack_id}/questions/incorrect-answers/batch?num_answers=3")
        
        if incorrect_response.status_code == 200:
            print(f"{Colors.GREEN}Successfully generated incorrect answers{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}Failed to generate incorrect answers: {incorrect_response.status_code}{Colors.ENDC}")
            return True  # Still return True since we have questions
    else:
        print(f"{Colors.FAIL}Failed to generate questions: {question_response.status_code}{Colors.ENDC}")
        return False

def check_questions(pack_id: str) -> bool:
    """Check if a pack has questions."""
    print(f"{Colors.HEADER}Checking if pack has questions...{Colors.ENDC}")
    
    response = requests.get(f"{BASE_URL}/packs/{pack_id}/questions/")
    
    if response.status_code == 200:
        result = response.json()
        questions = result.get("questions", [])
        question_count = len(questions)
        
        if question_count > 0:
            print(f"{Colors.GREEN}Pack has {question_count} questions{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.WARNING}Pack has no questions.{Colors.ENDC}")
            return False
    else:
        print(f"{Colors.FAIL}Failed to check questions: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return False

def create_game_session(pack_id: str, host_id: str, max_participants: int = 10, 
                        question_count: int = 5, time_limit: int = 30) -> Optional[Dict[str, Any]]:
    """Create a new game session."""
    data = {
        "pack_id": pack_id,
        "max_participants": max_participants,
        "question_count": question_count,
        "time_limit_seconds": time_limit
    }
    
    print(f"{Colors.HEADER}Creating game session for pack ID: {pack_id}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/games/create?user_id={host_id}", json=data)
    
    if response.status_code == 200:
        game_data = response.json()
        game_id = game_data.get("id")
        game_code = game_data.get("code")
        print(f"{Colors.GREEN}Successfully created game session with ID: {game_id}{Colors.ENDC}")
        print(f"{Colors.GREEN}Game code: {game_code}{Colors.ENDC}")
        return game_data
    else:
        print(f"{Colors.FAIL}Failed to create game session: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def join_game(game_code: str, user_id: str, display_name: str) -> Optional[Dict[str, Any]]:
    """Join an existing game session."""
    data = {
        "game_code": game_code,
        "display_name": display_name
    }
    
    print(f"{Colors.HEADER}Player '{display_name}' joining game with code: {game_code}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/games/join?user_id={user_id}", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"{Colors.GREEN}Successfully joined game. Player count: {result.get('participant_count', 0)}{Colors.ENDC}")
        return result
    else:
        print(f"{Colors.FAIL}Failed to join game: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def get_participants(game_id: str) -> List[Dict[str, Any]]:
    """Get the list of participants for a game."""
    print(f"{Colors.HEADER}Getting participants for game ID: {game_id}{Colors.ENDC}")
    
    response = requests.get(f"{BASE_URL}/games/{game_id}/participants")
    
    if response.status_code == 200:
        result = response.json()
        participants = result.get("participants", [])
        print(f"{Colors.GREEN}Game has {len(participants)} participants{Colors.ENDC}")
        
        # Display participant info
        for i, participant in enumerate(participants, 1):
            print(f"  {i}. {participant['display_name']} (Host: {participant['is_host']})")
        
        return participants
    else:
        print(f"{Colors.FAIL}Failed to get participants: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return []

def start_game(game_id: str, host_id: str) -> Optional[Dict[str, Any]]:
    """Start a game session."""
    print(f"{Colors.HEADER}Starting game with ID: {game_id}{Colors.ENDC}")
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/start?user_id={host_id}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"{Colors.GREEN}Successfully started game{Colors.ENDC}")
        
        # Display first question info
        question = result.get("current_question", {})
        print(f"\n{Colors.CYAN}Question {question.get('index', 0) + 1}:{Colors.ENDC}")
        print(f"{Colors.BLUE}{question.get('question_text', '')}{Colors.ENDC}")
        
        # Display options
        options = question.get("options", [])
        for i, option in enumerate(options):
            print(f"  {i + 1}. {option}")
        
        return result
    else:
        print(f"{Colors.FAIL}Failed to start game: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def submit_answer(game_id: str, participant_id: str, question_index: int, answer: str) -> Optional[Dict[str, Any]]:
    """Submit an answer for a question."""
    data = {
        "question_index": question_index,
        "answer": answer
    }
    
    print(f"{Colors.HEADER}Submitting answer for question {question_index + 1}: '{answer}'{Colors.ENDC}")
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/submit?participant_id={participant_id}", json=data)
    
    if response.status_code == 200:
        result = response.json()
        is_correct = result.get("is_correct", False)
        score = result.get("score", 0)
        
        if is_correct:
            print(f"{Colors.GREEN}Correct answer! +{score} points{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Incorrect answer. The correct answer was: {result.get('correct_answer', '')}{Colors.ENDC}")
        
        return result
    else:
        print(f"{Colors.FAIL}Failed to submit answer: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def next_question(game_id: str, host_id: str) -> Optional[Dict[str, Any]]:
    """Move to the next question or end the game."""
    print(f"{Colors.HEADER}Moving to next question...{Colors.ENDC}")
    
    response = requests.post(f"{BASE_URL}/games/{game_id}/next?user_id={host_id}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Check if game has ended
        if "final_results" in result:
            print(f"{Colors.GREEN}Game completed! Showing final results.{Colors.ENDC}")
            return result
        
        # Display next question info
        question = result.get("current_question", {})
        print(f"\n{Colors.CYAN}Question {question.get('index', 0) + 1}:{Colors.ENDC}")
        print(f"{Colors.BLUE}{question.get('question_text', '')}{Colors.ENDC}")
        
        # Display options
        options = question.get("options", [])
        for i, option in enumerate(options):
            print(f"  {i + 1}. {option}")
        
        return result
    else:
        print(f"{Colors.FAIL}Failed to move to next question: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def get_game_results(game_id: str) -> Optional[Dict[str, Any]]:
    """Get the final results of a completed game."""
    print(f"{Colors.HEADER}Getting final results for game ID: {game_id}{Colors.ENDC}")
    
    response = requests.get(f"{BASE_URL}/games/{game_id}/results")
    
    if response.status_code == 200:
        results = response.json()
        print(f"{Colors.GREEN}Successfully retrieved game results{Colors.ENDC}")
        
        # Display player rankings
        participants = results.get("participants", [])
        print(f"\n{Colors.CYAN}Final Rankings:{Colors.ENDC}")
        
        # Sort participants by score
        sorted_participants = sorted(participants, key=lambda p: p.get("score", 0), reverse=True)
        
        for i, participant in enumerate(sorted_participants, 1):
            print(f"{i}. {participant.get('display_name', 'Unknown')}: {participant.get('score', 0)} points")
        
        return results
    else:
        print(f"{Colors.FAIL}Failed to get game results: {response.status_code}{Colors.ENDC}")
        try:
            error_data = response.json()
            print_json(error_data)
        except:
            print(response.text)
        return None

def simulate_game_flow(
    pack_id: str, 
    num_players: int = 3, 
    question_count: int = 5, 
    time_limit: int = 30,
    host_id: Optional[str] = None,
    simulated_answers: bool = True,
    topic: Optional[str] = None
) -> None:
    """
    Simulate a complete game flow from creation to completion.
    
    Args:
        pack_id: ID of the pack to use
        num_players: Number of players to simulate
        question_count: Number of questions in the game
        time_limit: Time limit per question in seconds
        host_id: Optional host user ID (generated if not provided)
        simulated_answers: Whether to simulate random answers
        topic: Optional topic for question generation
    """
    # Step 1: Create temporary users for the host and participants
    # Create host user if not provided
    host_user = None
    if not host_id:
        host_user = create_temporary_user("Host")
        if not host_user:
            print(f"{Colors.FAIL}Failed to create host user. Exiting.{Colors.ENDC}")
            return
        host_id = host_user["id"]
        print(f"{Colors.CYAN}Created host user with ID: {host_id}{Colors.ENDC}")
    
    # Create temporary users for participants
    player_users = []
    for i in range(num_players - 1):  # -1 because the host is already counted
        player_name = generate_random_name()
        player_user = create_temporary_user(player_name)
        if player_user:
            player_users.append(player_user)
            print(f"{Colors.CYAN}Created player user: {player_name} with ID: {player_user['id']}{Colors.ENDC}")
    
    # Check if we created enough players
    if len(player_users) < (num_players - 1):
        print(f"{Colors.WARNING}Only created {len(player_users)} player users instead of {num_players - 1}{Colors.ENDC}")
    
    # Step 2: Check if pack has questions
    has_questions = check_questions(pack_id)
    
    # If not, generate content for the pack
    if not has_questions:
        print(f"{Colors.CYAN}Pack has no questions. Generating content...{Colors.ENDC}")
        if not generate_pack_content(pack_id, topic):
            print(f"{Colors.FAIL}Failed to generate pack content. Exiting.{Colors.ENDC}")
            return
    
    # Verify questions again
    if not check_questions(pack_id):
        print(f"{Colors.FAIL}Cannot create game: Pack still has no questions{Colors.ENDC}")
        return
    
    # Step 3: Create a game session
    game_session = create_game_session(
        pack_id=pack_id,
        host_id=host_id,
        max_participants=max(num_players, 2),  # Ensure at least 2 players
        question_count=question_count,
        time_limit=time_limit
    )
    
    if not game_session:
        print(f"{Colors.FAIL}Failed to create game session. Exiting.{Colors.ENDC}")
        return
    
    game_id = game_session["id"]
    game_code = game_session["code"]
    
    # Step 4: Have players join the game
    participant_ids = []
    player_names = []
    
    # Add the host first
    player_names.append("Host")
    
    # For each player, join the game
    for player_user in player_users:
        player_id = player_user["id"]
        player_name = player_user["displayname"]
        
        join_result = join_game(game_code, player_id, player_name)
        if join_result:
            player_names.append(player_name)
    
    # Get all participants to find their participant IDs
    participants = get_participants(game_id)
    participant_map = {}  # Map display names to participant IDs
    
    for participant in participants:
        participant_map[participant["display_name"]] = participant["id"]
    
    # Create a list of participant IDs in the same order as player_names
    for name in player_names:
        if name in participant_map:
            participant_ids.append(participant_map[name])
    
    # Step 5: Start the game
    start_result = start_game(game_id, host_id)
    if not start_result:
        print(f"{Colors.FAIL}Failed to start game. Exiting.{Colors.ENDC}")
        return
    
    current_question = start_result.get("current_question", {})
    question_index = current_question.get("index", 0)
    options = current_question.get("options", [])
    
    # Step 6: Play through all questions
    game_ended = False
    while not game_ended:
        # Simulate each player submitting an answer
        for i, (player_name, participant_id) in enumerate(zip(player_names, participant_ids)):
            # Optional delay to make the simulation more realistic
            time.sleep(0.5)
            
            if simulated_answers:
                # Randomly select an answer
                random_answer = random.choice(options)
                print(f"{Colors.HEADER}{player_name} selecting an answer...{Colors.ENDC}")
                submit_result = submit_answer(game_id, participant_id, question_index, random_answer)
            else:
                # If not simulating, prompt for input
                print(f"\n{Colors.HEADER}Enter answer for {player_name}:{Colors.ENDC}")
                for j, option in enumerate(options, 1):
                    print(f"{j}. {option}")
                try:
                    choice = int(input(f"Select option (1-{len(options)}): ")) - 1
                    if 0 <= choice < len(options):
                        submit_result = submit_answer(game_id, participant_id, question_index, options[choice])
                    else:
                        print(f"{Colors.WARNING}Invalid choice. Selecting first option.{Colors.ENDC}")
                        submit_result = submit_answer(game_id, participant_id, question_index, options[0])
                except ValueError:
                    print(f"{Colors.WARNING}Invalid input. Selecting first option.{Colors.ENDC}")
                    submit_result = submit_answer(game_id, participant_id, question_index, options[0])
            
            if not submit_result:
                print(f"{Colors.WARNING}Failed to submit answer for {player_name}{Colors.ENDC}")
        
        # Move to the next question (host action)
        time.sleep(1)
        next_result = next_question(game_id, host_id)
        
        if not next_result:
            print(f"{Colors.FAIL}Failed to move to next question. Exiting.{Colors.ENDC}")
            return
        
        # Check if the game has ended
        if "final_results" in next_result or next_result.get("game_complete", False):
            game_ended = True
            print(f"{Colors.GREEN}All questions completed!{Colors.ENDC}")
            break
        
        # Update for the next iteration
        current_question = next_result.get("current_question", {})
        question_index = current_question.get("index", 0)
        options = current_question.get("options", [])
    
    # Step 7: Get and display final results
    results = get_game_results(game_id)
    if results:
        print(f"\n{Colors.GREEN}Game completed successfully!{Colors.ENDC}")

def main():
    parser = argparse.ArgumentParser(description="Test the game APIs")
    parser.add_argument("--pack-id", "-p", help="ID of an existing pack to use")
    parser.add_argument("--pack-name", "-n", help="Name for a new pack (if pack-id not provided)")
    parser.add_argument("--topic", "-t", help="Topic for question generation", default="World History")
    parser.add_argument("--host-id", "-H", help="ID of the host user (generated if not provided)")
    parser.add_argument("--players", "-P", type=int, default=3, help="Number of players to simulate")
    parser.add_argument("--questions", "-q", type=int, default=5, help="Number of questions per game")
    parser.add_argument("--time-limit", "-T", type=int, default=30, help="Time limit per question in seconds")
    parser.add_argument("--manual", "-m", action="store_true", help="Manually input answers instead of simulating")
    args = parser.parse_args()
    
    # Validate arguments
    if not args.pack_id and not args.pack_name:
        print(f"{Colors.FAIL}Error: Either --pack-id or --pack-name must be provided{Colors.ENDC}")
        parser.print_help()
        return
    
    # Get or create a pack
    pack = None
    if args.pack_id:
        pack = create_or_get_pack(pack_id=args.pack_id)
    else:
        pack = create_or_get_pack(pack_name=args.pack_name)
    
    if not pack:
        print(f"{Colors.FAIL}Failed to get or create a pack. Exiting.{Colors.ENDC}")
        return
    
    # Run the game simulation
    simulate_game_flow(
        pack_id=pack["id"],
        num_players=args.players,
        question_count=args.questions,
        time_limit=args.time_limit,
        host_id=args.host_id,
        simulated_answers=not args.manual,
        topic=args.topic
    )

if __name__ == "__main__":
    main()