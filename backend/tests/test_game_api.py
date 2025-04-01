# backend/tests/test_game_api.py
import unittest
import uuid
from fastapi.testclient import TestClient
import pytest
import asyncio
from typing import Dict, Any, List

# Import the FastAPI app
from backend.src.main import app
from backend.src.models.game_session import GameStatus

# Create test client
client = TestClient(app)

class TestGameAPI(unittest.TestCase):
    """Test suite for Game API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Generate unique IDs for this test run
        self.user_id = str(uuid.uuid4())
        self.host_user_id = str(uuid.uuid4())
        self.pack_id = None  # Will be set after finding a valid pack
        
        # Game session data
        self.game_id = None
        self.game_code = None
        self.participant_id = None
        
        # Find a valid pack to use for testing
        self._find_valid_pack()
    
    def _find_valid_pack(self):
        """Find a valid pack to use for tests"""
        # Get list of packs
        response = client.get("/api/packs/")
        self.assertEqual(response.status_code, 200)
        
        packs = response.json()
        if packs["total"] > 0:
            self.pack_id = packs["packs"][0]["id"]
        else:
            # Create a pack if none exist
            pack_data = {
                "name": f"Test Pack {uuid.uuid4()}",
                "description": "Test pack for API testing",
                "price": 0.0,
                "creator_type": "SYSTEM"
            }
            response = client.post("/api/packs/", json=pack_data)
            self.assertEqual(response.status_code, 201)
            self.pack_id = response.json()["id"]
            
            # Generate some questions for the pack
            topic_data = {
                "num_topics": 1,
                "predefined_topic": "General Knowledge"
            }
            client.post(f"/api/packs/{self.pack_id}/topics/", json=topic_data)
            
            # Generate questions
            question_data = {
                "pack_topic": "General Knowledge",
                "difficulty": "EASY",
                "num_questions": 5
            }
            client.post(f"/api/packs/{self.pack_id}/questions/", json=question_data)
    
    def test_01_create_game(self):
        """Test creating a new game session"""
        # Create game session
        game_data = {
            "pack_id": self.pack_id,
            "max_participants": 5,
            "question_count": 5,
            "time_limit_seconds": 30
        }
        
        response = client.post(
            f"/api/games/create?user_id={self.host_user_id}",
            json=game_data
        )
        
        self.assertEqual(response.status_code, 200)
        game_session = response.json()
        
        # Store game details for later tests
        self.game_id = game_session["id"]
        self.game_code = game_session["code"]
        
        # Verify game properties
        self.assertEqual(game_session["status"], GameStatus.PENDING.value)
        self.assertEqual(game_session["pack_id"], self.pack_id)
        self.assertEqual(game_session["max_participants"], 5)
        self.assertEqual(game_session["question_count"], 5)
        self.assertEqual(game_session["time_limit_seconds"], 30)
        self.assertEqual(game_session["is_host"], True)
        
        print(f"Created game session {self.game_id} with code {self.game_code}")
    
    def test_02_join_game(self):
        """Test joining an existing game session"""
        # Create game if not already created
        if not self.game_code:
            self.test_01_create_game()
        
        # Join the game
        join_data = {
            "game_code": self.game_code,
            "display_name": "Test Player"
        }
        
        response = client.post(
            f"/api/games/join?user_id={self.user_id}",
            json=join_data
        )
        
        self.assertEqual(response.status_code, 200)
        game_session = response.json()
        
        # Verify game properties
        self.assertEqual(game_session["code"], self.game_code)
        self.assertEqual(game_session["status"], GameStatus.PENDING.value)
        self.assertEqual(game_session["is_host"], False)
        
        # Get participants to find our participant ID
        response = client.get(f"/api/games/{self.game_id}/participants")
        self.assertEqual(response.status_code, 200)
        
        participants = response.json()["participants"]
        for p in participants:
            if p["display_name"] == "Test Player" and not p["is_host"]:
                self.participant_id = p["id"]
                break
        
        self.assertIsNotNone(self.participant_id)
        print(f"Joined game as participant {self.participant_id}")
    
    def test_03_start_game(self):
        """Test starting a game session"""
        # Create and join game if needed
        if not self.game_code:
            self.test_01_create_game()
            self.test_02_join_game()
        
        # Start the game
        response = client.post(
            f"/api/games/{self.game_id}/start?user_id={self.host_user_id}"
        )
        
        self.assertEqual(response.status_code, 200)
        game_data = response.json()
        
        # Verify game status
        self.assertEqual(game_data["status"], GameStatus.ACTIVE.value)
        
        # Verify first question
        self.assertIn("current_question", game_data)
        self.assertEqual(game_data["current_question"]["index"], 0)
        self.assertIsNotNone(game_data["current_question"]["question_text"])
        self.assertGreater(len(game_data["current_question"]["options"]), 1)
        
        print("Game started successfully with first question")
    
    def test_04_submit_answer(self):
        """Test submitting an answer to a question"""
        # Ensure game is started
        if not self.participant_id:
            self.test_01_create_game()
            self.test_02_join_game()
            self.test_03_start_game()
        
        # Submit an answer (first option)
        # Get current question first
        response = client.post(f"/api/games/{self.game_id}/start?user_id={self.host_user_id}")
        question = response.json()["current_question"]
        
        answer_data = {
            "question_index": question["index"],
            "answer": question["options"][0]  # Choose the first option
        }
        
        response = client.post(
            f"/api/games/{self.game_id}/submit?participant_id={self.participant_id}",
            json=answer_data
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify result structure
        self.assertIn("is_correct", result)
        self.assertIn("correct_answer", result)
        self.assertIn("score", result)
        self.assertIn("total_score", result)
        
        print(f"Answer submitted - Correct: {result['is_correct']}, Score: {result['score']}")
    
    def test_05_next_question(self):
        """Test advancing to the next question"""
        # Ensure game is started and answer submitted
        if not self.participant_id:
            self.test_01_create_game()
            self.test_02_join_game()
            self.test_03_start_game()
            self.test_04_submit_answer()
        
        # Advance to next question
        response = client.post(
            f"/api/games/{self.game_id}/next?user_id={self.host_user_id}"
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Check if game is complete or we have a next question
        if result.get("game_complete"):
            self.assertIn("results", result)
            print("Game completed, results retrieved")
        else:
            self.assertIn("next_question", result)
            self.assertEqual(result["next_question"]["index"], 1)  # Should be second question
            print("Advanced to next question")
    
    def test_06_get_game_results(self):
        """Test getting game results"""
        # Play through all questions first
        if not self.game_id:
            self.test_01_create_game()
            self.test_02_join_game()
            self.test_03_start_game()
        
        # Force game completion by advancing through all questions
        for _ in range(5):  # We created a game with 5 questions
            # Submit an answer
            response = client.post(f"/api/games/{self.game_id}/start?user_id={self.host_user_id}")
            if response.status_code != 200:
                continue
                
            question = response.json().get("current_question")
            if not question:
                break
                
            answer_data = {
                "question_index": question["index"],
                "answer": question["options"][0]
            }
            
            client.post(
                f"/api/games/{self.game_id}/submit?participant_id={self.participant_id}",
                json=answer_data
            )
            
            # Move to next question
            client.post(f"/api/games/{self.game_id}/next?user_id={self.host_user_id}")
        
        # Get results
        response = client.get(f"/api/games/{self.game_id}/results")
        
        self.assertEqual(response.status_code, 200)
        results = response.json()
        
        # Verify results structure
        self.assertEqual(results["game_id"], self.game_id)
        self.assertEqual(results["game_code"], self.game_code)
        self.assertIn("participants", results)
        self.assertIn("questions", results)
        self.assertEqual(results["total_questions"], 5)
        
        print("Game results retrieved successfully")
    
    def test_07_cancel_game(self):
        """Test cancelling a game"""
        # Create a new game to cancel
        self.test_01_create_game()
        
        # Cancel the game
        response = client.post(
            f"/api/games/{self.game_id}/cancel?user_id={self.host_user_id}"
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify cancellation
        self.assertEqual(result["status"], GameStatus.CANCELLED.value)
        
        print("Game cancelled successfully")
    
    def test_08_list_games(self):
        """Test listing user's games"""
        # Create game if not already created
        if not self.host_user_id:
            self.test_01_create_game()
        
        # List games
        response = client.get(
            f"/api/games/list?user_id={self.host_user_id}&include_completed=true"
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify response structure
        self.assertIn("total", result)
        self.assertIn("games", result)
        self.assertGreater(result["total"], 0)
        
        print(f"Listed {result['total']} games for the user")

if __name__ == "__main__":
    # Run tests in order
    unittest.main()