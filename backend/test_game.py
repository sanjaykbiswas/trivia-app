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
    try:
        print(json.dumps(data, indent=2))
    except TypeError:
        print(str(data))


def generate_random_name(prefix: str = "Player") -> str:
    """Generate a random name for a player or session."""
    random_suffix = ''.join(random.choice(string.ascii_lowercase) for _ in range(4))
    return f"{prefix}_{random_suffix}"

def create_temporary_user(display_name: Optional[str] = None, is_temporary: bool = True) -> Optional[Dict[str, Any]]:
    """Create a temporary user for testing."""
    if not display_name:
        display_name = generate_random_name("User")

    # --- FIX: Explicitly set None for optional fields ---
    data = {
        "displayname": display_name,
        "is_temporary": is_temporary,
        "email": None,
        "auth_provider": None,
        "auth_id": None
    }
    # --- END FIX ---

    print(f"{Colors.HEADER}Creating temporary user: {display_name}{Colors.ENDC}")
    response = requests.post(f"{BASE_URL}/users/", json=data)

    if response.status_code == 201:
        user_data = response.json()
        print(f"{Colors.GREEN}Successfully created user with ID: {user_data['id']}{Colors.ENDC}")
        return user_data
    else:
        print(f"{Colors.FAIL}Failed to create user: {response.status_code}{Colors.ENDC}")
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
            # --- FIX: Handle potential non-JSON error response ---
            try:
                error_data = response.json()
                print_json(error_data)
            except json.JSONDecodeError:
                print(f"Raw error response: {response.text}")
            # --- END FIX ---
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
        # Handle 400 Bad Request if pack already exists by name
        elif response.status_code == 400:
             print(f"{Colors.WARNING}Pack '{pack_name}' might already exist. Trying to fetch it.{Colors.ENDC}")
             # Attempt to fetch all packs and find by name (less efficient but works)
             list_response = requests.get(f"{BASE_URL}/packs/")
             if list_response.status_code == 200:
                 packs = list_response.json().get("packs", [])
                 for p in packs:
                     if p['name'].lower() == pack_name.lower():
                         print(f"{Colors.GREEN}Found existing pack with ID: {p['id']}{Colors.ENDC}")
                         return p
                 print(f"{Colors.FAIL}Could not find pack '{pack_name}' after creation attempt failed.{Colors.ENDC}")
                 return None
             else:
                print(f"{Colors.FAIL}Failed to list packs to find existing one: {list_response.status_code}{Colors.ENDC}")
                return None
        else:
            print(f"{Colors.FAIL}Failed to create pack: {response.status_code}{Colors.ENDC}")
            # --- FIX: Handle potential non-JSON error response ---
            try:
                error_data = response.json()
                print_json(error_data)
            except json.JSONDecodeError:
                print(f"Raw error response: {response.text}")
            # --- END FIX ---
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
        try:
            print_json(topic_response.json())
        except json.JSONDecodeError:
            print(f"Raw error: {topic_response.text}")
        return False

    # Generate difficulty descriptions
    print(f"{Colors.HEADER}Generating difficulty descriptions...{Colors.ENDC}")
    difficulty_data = {
        "force_regenerate": True
    }
    difficulty_response = requests.post(f"{BASE_URL}/packs/{pack_id}/difficulties/", json=difficulty_data)

    if difficulty_response.status_code != 200:
        print(f"{Colors.FAIL}Failed to generate difficulties: {difficulty_response.status_code}{Colors.ENDC}")
        try:
            print_json(difficulty_response.json())
        except json.JSONDecodeError:
            print(f"Raw error: {difficulty_response.text}")
        return False

    # Generate questions
    print(f"{Colors.HEADER}Generating questions for topic '{topic}'...{Colors.ENDC}")
    question_data = {
        "pack_topic": topic,
        "difficulty": "mixed",
        "num_questions": 10, # Generate enough questions for the game
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
            try:
                print_json(incorrect_response.json())
            except json.JSONDecodeError:
                print(f"Raw error: {incorrect_response.text}")
            return True  # Still return True since we have questions
    else:
        print(f"{Colors.FAIL}Failed to generate questions: {question_response.status_code}{Colors.ENDC}")
        try:
            print_json(question_response.json())
        except json.JSONDecodeError:
            print(f"Raw error: {question_response.text}")
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
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
            print(f"  {i}. {participant['display_name']} (Host: {participant['is_host']}) ID: {participant['id']}") # Added ID

        return participants
    else:
        print(f"{Colors.FAIL}Failed to get participants: {response.status_code}{Colors.ENDC}")
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
        return None

def submit_answer(game_id: str, participant_id: str, question_index: int, answer: str) -> Optional[Dict[str, Any]]:
    """Submit an answer for a question."""
    data = {
        "question_index": question_index,
        "answer": answer
    }

    print(f"{Colors.HEADER}Submitting answer for question {question_index + 1}: '{answer}' (Participant: {participant_id}){Colors.ENDC}")

    response = requests.post(f"{BASE_URL}/games/{game_id}/submit?participant_id={participant_id}", json=data)

    if response.status_code == 200:
        result = response.json()
        is_correct = result.get("is_correct", False)
        score = result.get("score", 0)
        total_score = result.get("total_score", "N/A")

        if is_correct:
            print(f"{Colors.GREEN}Correct answer! +{score} points. Total: {total_score}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Incorrect answer. Correct: {result.get('correct_answer', '')}. Total: {total_score}{Colors.ENDC}")

        return result
    else:
        print(f"{Colors.FAIL}Failed to submit answer: {response.status_code}{Colors.ENDC}")
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
        return None

def next_question(game_id: str, host_id: str) -> Optional[Dict[str, Any]]:
    """Move to the next question or end the game."""
    print(f"{Colors.HEADER}Moving to next question (Host action)...{Colors.ENDC}")

    response = requests.post(f"{BASE_URL}/games/{game_id}/next?user_id={host_id}")

    if response.status_code == 200:
        result = response.json()

        # Check if game has ended (key might be 'results' or 'game_complete')
        if result.get("game_complete", False):
            print(f"{Colors.GREEN}Game completed! Final results available.{Colors.ENDC}")
            return result # Return the result which should contain final details or a flag

        # Display next question info
        question = result.get("next_question") # Key changed in service
        if question:
             print(f"\n{Colors.CYAN}Question {question.get('index', 0) + 1}:{Colors.ENDC}")
             print(f"{Colors.BLUE}{question.get('question_text', '')}{Colors.ENDC}")

             # Display options
             options = question.get("options", [])
             for i, option in enumerate(options):
                 print(f"  {i + 1}. {option}")
        else:
             print(f"{Colors.WARNING}No next question data found in response.{Colors.ENDC}")
             print_json(result) # Print the unexpected result


        return result
    else:
        print(f"{Colors.FAIL}Failed to move to next question: {response.status_code}{Colors.ENDC}")
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
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
        # --- FIX: Handle potential non-JSON error response ---
        try:
            error_data = response.json()
            print_json(error_data)
        except json.JSONDecodeError:
            print(f"Raw error response: {response.text}")
        # --- END FIX ---
        return None

# ... (simulate_game_flow function remains largely the same, but ensure participant IDs are correctly retrieved)
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
    """
    # Step 1: Create temporary users
    host_user = None
    if not host_id:
        host_user = create_temporary_user("Host")
        if not host_user:
            print(f"{Colors.FAIL}Failed to create host user. Exiting.{Colors.ENDC}")
            return
        host_id = host_user["id"]
        print(f"{Colors.CYAN}Created host user with ID: {host_id}{Colors.ENDC}")

    player_users = []
    for i in range(num_players - 1):
        player_name = generate_random_name()
        player_user = create_temporary_user(player_name)
        if player_user:
            player_users.append(player_user)
            print(f"{Colors.CYAN}Created player user: {player_name} with ID: {player_user['id']}{Colors.ENDC}")

    if len(player_users) < (num_players - 1):
        print(f"{Colors.WARNING}Only created {len(player_users)} player users instead of {num_players - 1}{Colors.ENDC}")

    # Step 2: Check/Generate Pack Content
    has_questions = check_questions(pack_id)
    if not has_questions:
        print(f"{Colors.CYAN}Pack has no questions. Generating content...{Colors.ENDC}")
        if not generate_pack_content(pack_id, topic):
            print(f"{Colors.FAIL}Failed to generate pack content. Exiting.{Colors.ENDC}")
            return

    if not check_questions(pack_id):
        print(f"{Colors.FAIL}Cannot create game: Pack still has no questions{Colors.ENDC}")
        return

    # Step 3: Create Game Session
    game_session = create_game_session(
        pack_id=pack_id,
        host_id=host_id,
        max_participants=max(num_players, 2),
        question_count=question_count,
        time_limit=time_limit
    )
    if not game_session: return
    game_id = game_session["id"]
    game_code = game_session["code"]

    # Step 4: Join Game
    all_display_names = ["Host"] + [p["displayname"] for p in player_users]
    for player_user in player_users:
        join_game(game_code, player_user["id"], player_user["displayname"])
        time.sleep(0.2) # Small delay between joins

    # Get Participant IDs (Crucial Step)
    participants = get_participants(game_id)
    if len(participants) != num_players:
         print(f"{Colors.WARNING}Expected {num_players} participants, but found {len(participants)}. Continuing cautiously...{Colors.ENDC}")

    participant_map = {p["display_name"]: p["id"] for p in participants}
    ordered_participant_ids = []
    host_participant_id = None
    for name in all_display_names:
        p_id = participant_map.get(name)
        if p_id:
            ordered_participant_ids.append(p_id)
            # Find the host's participant ID specifically
            for p in participants:
                if p["id"] == p_id and p["is_host"]:
                    host_participant_id = p_id
                    break
        else:
            print(f"{Colors.WARNING}Could not find participant ID for {name}{Colors.ENDC}")

    if len(ordered_participant_ids) != num_players:
        print(f"{Colors.FAIL}Could not correctly map all participants. Exiting.{Colors.ENDC}")
        return

    if not host_participant_id:
         # Fallback: assume first participant is host if specific lookup failed
         host_participant_data = next((p for p in participants if p["is_host"]), None)
         if host_participant_data:
             host_participant_id = host_participant_data["id"]
             print(f"{Colors.WARNING}Could not map host by name, found host participant ID: {host_participant_id} by flag.{Colors.ENDC}")
         else:
             print(f"{Colors.FAIL}Could not determine host participant ID. Exiting.{Colors.ENDC}")
             return


    print(f"{Colors.CYAN}All {len(ordered_participant_ids)} players ready.{Colors.ENDC}")

    # Step 5: Start Game
    start_result = start_game(game_id, host_id) # Host starts using their user_id
    if not start_result: return

    current_question = start_result.get("current_question", {})
    question_index = current_question.get("index", 0)
    options = current_question.get("options", [])

    # Step 6: Play Loop
    game_ended = False
    while not game_ended:
        print(f"\n--- Question {question_index + 1} ---")
        # Simulate submissions
        for i, participant_id in enumerate(ordered_participant_ids):
            player_name = all_display_names[i] # Get name based on order
            time.sleep(0.3 + random.random() * 0.5) # Simulate thinking time

            if simulated_answers and options:
                random_answer = random.choice(options)
                print(f"  {player_name} chooses '{random_answer}'")
                submit_answer(game_id, participant_id, question_index, random_answer)
            elif not simulated_answers and options:
                # Manual input section (simplified)
                print(f"\n{Colors.HEADER}Enter answer for {player_name}:{Colors.ENDC}")
                for j, option in enumerate(options, 1):
                    print(f"{j}. {option}")
                try:
                    choice = int(input(f"Select option (1-{len(options)}): ")) - 1
                    chosen_answer = options[choice] if 0 <= choice < len(options) else options[0]
                except (ValueError, IndexError):
                    print(f"{Colors.WARNING}Invalid input. Selecting first option.{Colors.ENDC}")
                    chosen_answer = options[0]
                submit_answer(game_id, participant_id, question_index, chosen_answer)
            else:
                 print(f"{Colors.WARNING}No options available for question {question_index + 1}, cannot submit.{Colors.ENDC}")


        # Move to next question (Host action)
        print("\nHost advancing to next question...")
        time.sleep(1)
        next_result = next_question(game_id, host_id)

        if not next_result:
            print(f"{Colors.FAIL}Failed to move to next question. Exiting simulation.{Colors.ENDC}")
            return

        if next_result.get("game_complete", False):
            game_ended = True
            print(f"{Colors.GREEN}Game ending signal received.{Colors.ENDC}")
        else:
            next_q_data = next_result.get("next_question")
            if next_q_data:
                question_index = next_q_data.get("index", question_index + 1)
                options = next_q_data.get("options", [])
            else:
                 print(f"{Colors.FAIL}Error: No 'next_question' data in response but game not complete. Exiting.{Colors.ENDC}")
                 print_json(next_result)
                 return


    # Step 7: Get Final Results
    get_game_results(game_id)
    print(f"\n{Colors.GREEN}Game simulation finished successfully!{Colors.ENDC}")


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

    if not args.pack_id and not args.pack_name:
        print(f"{Colors.FAIL}Error: Either --pack-id or --pack-name must be provided{Colors.ENDC}")
        parser.print_help()
        return

    pack = None
    if args.pack_id:
        pack = create_or_get_pack(pack_id=args.pack_id)
    else:
        pack = create_or_get_pack(pack_name=args.pack_name)

    if not pack:
        print(f"{Colors.FAIL}Failed to get or create a pack. Exiting.{Colors.ENDC}")
        return

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