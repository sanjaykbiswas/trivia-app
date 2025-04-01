# backend/src/services/game_service.py
import random
import string
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from ..models.game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from ..models.game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..models.question import Question
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class GameService:
    """
    Service for game management operations.
    
    Handles business logic related to creating, joining, and playing
    multiplayer trivia games.
    """
    
    def __init__(
        self,
        game_session_repository: GameSessionRepository,
        game_participant_repository: GameParticipantRepository,
        game_question_repository: GameQuestionRepository,
        question_repository: QuestionRepository,
        incorrect_answers_repository: IncorrectAnswersRepository
    ):
        """
        Initialize the service with required repositories.
        
        Args:
            game_session_repository: Repository for game session operations
            game_participant_repository: Repository for game participant operations
            game_question_repository: Repository for game question operations
            question_repository: Repository for question operations
            incorrect_answers_repository: Repository for incorrect answers operations
        """
        self.game_session_repo = game_session_repository
        self.game_participant_repo = game_participant_repository
        self.game_question_repo = game_question_repository
        self.question_repo = question_repository
        self.incorrect_answers_repo = incorrect_answers_repository
    
    async def create_game_session(
        self, 
        host_user_id: str,
        pack_id: str,
        max_participants: int = 10,
        question_count: int = 10,
        time_limit_seconds: int = 0
    ) -> GameSession:
        """
        Create a new game session.
        
        Args:
            host_user_id: ID of the user creating the game
            pack_id: ID of the question pack to use
            max_participants: Maximum number of participants allowed
            question_count: Number of questions to include
            time_limit_seconds: Time limit per question (0 for no limit)
            
        Returns:
            Created GameSession object
        """
        # Ensure IDs are valid UUID strings
        host_user_id = ensure_uuid(host_user_id)
        pack_id = ensure_uuid(pack_id)
        
        # Generate a unique game code
        game_code = await self._generate_unique_game_code()
        
        # Create the game session
        game_session_data = GameSessionCreate(
            code=game_code,
            host_user_id=host_user_id,
            pack_id=pack_id,
            max_participants=max_participants,
            question_count=question_count,
            time_limit_seconds=time_limit_seconds,
            status=GameStatus.PENDING
        )
        
        game_session = await self.game_session_repo.create(obj_in=game_session_data)
        logger.info(f"Created game session with ID: {game_session.id}, code: {game_session.code}")
        
        # Add the host as a participant
        host_participant_data = GameParticipantCreate(
            game_session_id=game_session.id,
            user_id=host_user_id,
            display_name="Host",  # This would typically come from the user profile
            is_host=True
        )
        
        await self.game_participant_repo.create(obj_in=host_participant_data)
        
        return game_session
    
    async def _generate_unique_game_code(self, length: int = 6) -> str:
        """
        Generate a unique, easy-to-read game code.
        
        Args:
            length: Length of the code to generate
            
        Returns:
            Unique game code string
        """
        # Characters that are easy to read and distinguish
        characters = string.ascii_uppercase + string.digits
        # Exclude easily confused characters
        characters = characters.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        
        max_attempts = 10
        for _ in range(max_attempts):
            # Generate a random code
            code = ''.join(random.choice(characters) for _ in range(length))
            
            # Check if it's already in use
            existing_session = await self.game_session_repo.get_by_code(code)
            if not existing_session:
                return code
        
        # If we couldn't generate a unique code in max_attempts, use a longer code
        return await self._generate_unique_game_code(length + 1)
    
    async def join_game(
        self,
        game_code: str,
        user_id: str,
        display_name: str
    ) -> Tuple[GameSession, GameParticipant]:
        """
        Join an existing game session.
        
        Args:
            game_code: Code for the game to join
            user_id: ID of the user joining
            display_name: Display name to use in the game
            
        Returns:
            Tuple of (GameSession, GameParticipant)
            
        Raises:
            ValueError: If the game cannot be joined
        """
        # Ensure user_id is a valid UUID string
        user_id = ensure_uuid(user_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_code(game_code)
        if not game_session:
            raise ValueError(f"Game with code {game_code} not found")
        
        # Check if the game is joinable
        if game_session.status != GameStatus.PENDING:
            raise ValueError(f"Game with code {game_code} is not accepting new players")
        
        # Check if there's room for more participants
        participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
        if len(participants) >= game_session.max_participants:
            raise ValueError(f"Game with code {game_code} is full")
        
        # Check if user is already a participant
        for participant in participants:
            if participant.user_id == user_id:
                # User is already in this game
                return game_session, participant
        
        # Add user as a participant
        participant_data = GameParticipantCreate(
            game_session_id=game_session.id,
            user_id=user_id,
            display_name=display_name,
            is_host=False
        )
        
        participant = await self.game_participant_repo.create(obj_in=participant_data)
        logger.info(f"User {user_id} joined game {game_code} as participant {participant.id}")
        
        return game_session, participant
    
    async def start_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        """
        Start a game session.
        
        Args:
            game_session_id: ID of the game to start
            host_user_id: ID of the user trying to start the game (must be host)
            
        Returns:
            Updated GameSession object
            
        Raises:
            ValueError: If the game cannot be started
        """
        # Ensure IDs are valid UUID strings
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")
        
        # Verify the user is the host
        if game_session.host_user_id != host_user_id:
            raise ValueError("Only the host can start the game")
        
        # Check if the game is in a valid state to start
        if game_session.status != GameStatus.PENDING:
            raise ValueError(f"Game cannot be started (current status: {game_session.status})")
        
        # Select questions for the game
        questions = await self._select_questions_for_game(
            pack_id=game_session.pack_id,
            count=game_session.question_count
        )
        
        if len(questions) < game_session.question_count:
            logger.warning(
                f"Only {len(questions)} questions available for game {game_session_id}, " +
                f"requested {game_session.question_count}"
            )
        
        if not questions:
            raise ValueError("No questions available for this game")
        
        # Create game question records
        for index, question in enumerate(questions):
            question_data = GameQuestionCreate(
                game_session_id=game_session_id,
                question_id=question.id,
                question_index=index
            )
            await self.game_question_repo.create(obj_in=question_data)
        
        # Update game status to active
        updated_game = await self.game_session_repo.update_game_status(
            game_id=game_session_id,
            status=GameStatus.ACTIVE
        )
        
        # Start the first question
        await self._advance_to_next_question(game_session_id, 0)
        
        logger.info(f"Game {game_session_id} started with {len(questions)} questions")
        
        return updated_game
    
    async def _select_questions_for_game(
        self, 
        pack_id: str, 
        count: int
    ) -> List[Question]:
        """
        Select questions for a game from a pack.
        
        Args:
            pack_id: ID of the pack to select questions from
            count: Number of questions to select
            
        Returns:
            List of Question objects
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        # Get all questions for the pack
        all_questions = await self.question_repo.get_by_pack_id(pack_id)
        
        # If we don't have enough questions, use all available
        if len(all_questions) <= count:
            return all_questions
        
        # Otherwise, select random questions
        return random.sample(all_questions, count)
    
    async def _advance_to_next_question(
        self, 
        game_session_id: str, 
        next_index: Optional[int] = None
    ) -> Optional[GameQuestion]:
        """
        Advance to the next question in a game.
        
        Args:
            game_session_id: ID of the game session
            next_index: Index of the next question (if None, current index + 1)
            
        Returns:
            The next GameQuestion or None if game is complete
        """
        # Ensure game_session_id is a valid UUID string
        game_session_id = ensure_uuid(game_session_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            logger.error(f"Game session {game_session_id} not found")
            return None
        
        # Determine the next question index
        if next_index is None:
            next_index = game_session.current_question_index + 1
        
        # Get all game questions
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)
        
        # Check if we've reached the end of the game
        if next_index >= len(game_questions):
            # Game is complete
            await self.game_session_repo.update_game_status(
                game_id=game_session_id,
                status=GameStatus.COMPLETED
            )
            logger.info(f"Game {game_session_id} completed (all questions answered)")
            return None
        
        # Update the current question index
        await self.game_session_repo.update(
            id=game_session_id,
            obj_in=GameSessionUpdate(current_question_index=next_index)
        )
        
        # Get the next question
        next_question = await self.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_session_id,
            question_index=next_index
        )
        
        if next_question:
            # Mark the question as started
            await self.game_question_repo.start_question(next_question.id)
        
        return next_question
    
    async def submit_answer(
        self, 
        game_session_id: str, 
        participant_id: str, 
        question_index: int, 
        answer: str
    ) -> Dict[str, Any]:
        """
        Submit an answer for a question.
        
        Args:
            game_session_id: ID of the game session
            participant_id: ID of the participant submitting the answer
            question_index: Index of the question being answered
            answer: The answer being submitted
            
        Returns:
            Dictionary with result information
            
        Raises:
            ValueError: If the answer cannot be submitted
        """
        # Ensure IDs are valid UUID strings
        game_session_id = ensure_uuid(game_session_id)
        participant_id = ensure_uuid(participant_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")
        
        # Check if the game is active
        if game_session.status != GameStatus.ACTIVE:
            raise ValueError(f"Game is not active (status: {game_session.status})")
        
        # Verify the participant exists in this game
        participant = await self.game_participant_repo.get_by_id(participant_id)
        if not participant or participant.game_session_id != game_session_id:
            raise ValueError(f"Participant {participant_id} not found in game {game_session_id}")
        
        # Get the game question
        game_question = await self.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_session_id,
            question_index=question_index
        )
        
        if not game_question:
            raise ValueError(f"Question index {question_index} not found in game {game_session_id}")
        
        # Check if this is the current question
        if game_session.current_question_index != question_index:
            raise ValueError(
                f"Cannot answer question {question_index}, " +
                f"current question is {game_session.current_question_index}"
            )
        
        # Check if the question is still active (has start_time but no end_time)
        if not game_question.start_time:
            raise ValueError(f"Question {question_index} has not started yet")
        
        if game_question.end_time:
            raise ValueError(f"Question {question_index} has already ended")
        
        # Record the participant's answer
        await self.game_question_repo.record_participant_answer(
            question_id=game_question.id,
            participant_id=participant_id,
            answer=answer
        )
        
        # Get the original question to check the answer
        original_question = await self.question_repo.get_by_id(game_question.question_id)
        if not original_question:
            logger.error(f"Original question {game_question.question_id} not found")
            return {"success": False, "error": "Question not found"}
        
        # Check if the answer is correct
        is_correct = answer.lower().strip() == original_question.answer.lower().strip()
        
        # Calculate score based on time taken (faster answers get more points)
        score = 0
        if is_correct:
            max_score = 1000
            now = datetime.utcnow()
            start_time = game_question.start_time
            
            # Basic scoring: max_score if answered immediately, decreasing over time
            if start_time:
                seconds_taken = (now - start_time).total_seconds()
                time_factor = max(0, 1 - (seconds_taken / 30))  # 30 seconds to get minimum score
                score = int(max_score * time_factor)
                
                # Ensure minimum score for correct answers
                score = max(score, 100)
        
        # Record the participant's score
        await self.game_question_repo.record_participant_score(
            question_id=game_question.id,
            participant_id=participant_id,
            score=score
        )
        
        # Update the participant's total score
        new_total_score = participant.score + score
        await self.game_participant_repo.update_score(
            participant_id=participant_id,
            new_score=new_total_score
        )
        
        # Return the result
        return {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": original_question.answer,
            "score": score,
            "total_score": new_total_score
        }
    
    async def end_current_question(
        self, 
        game_session_id: str, 
        host_user_id: str
    ) -> Dict[str, Any]:
        """
        End the current question and advance to the next one.
        
        Args:
            game_session_id: ID of the game session
            host_user_id: ID of the host user (for permission check)
            
        Returns:
            Dictionary with information about the next question
            
        Raises:
            ValueError: If the question cannot be ended
        """
        # Ensure IDs are valid UUID strings
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")
        
        # Verify the user is the host
        if game_session.host_user_id != host_user_id:
            raise ValueError("Only the host can end the current question")
        
        # Check if the game is active
        if game_session.status != GameStatus.ACTIVE:
            raise ValueError(f"Game is not active (status: {game_session.status})")
        
        # Get the current question
        current_index = game_session.current_question_index
        current_question = await self.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_session_id,
            question_index=current_index
        )
        
        if not current_question:
            raise ValueError(f"Current question (index {current_index}) not found")
        
        # Mark the current question as ended
        if current_question.start_time and not current_question.end_time:
            await self.game_question_repo.end_question(current_question.id)
        
        # Advance to the next question
        next_question = await self._advance_to_next_question(game_session_id)
        
        if next_question:
            # Get the original question data for the next question
            original_question = await self.question_repo.get_by_id(next_question.question_id)
            if not original_question:
                logger.error(f"Original question {next_question.question_id} not found")
                return {"game_complete": False, "error": "Question not found"}
            
            # Get incorrect answers for the question
            incorrect_answers = await self.incorrect_answers_repo.get_by_question_id(next_question.question_id)
            incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []
            
            # Combine correct and incorrect answers and shuffle
            all_options = [original_question.answer] + incorrect_options
            random.shuffle(all_options)
            
            return {
                "game_complete": False,
                "next_question": {
                    "index": next_question.question_index,
                    "question_text": original_question.question,
                    "options": all_options,
                    "time_limit": game_session.time_limit_seconds
                }
            }
        else:
            # Game is complete
            results = await self.get_game_results(game_session_id)
            return {
                "game_complete": True,
                "results": results
            }
    
    async def get_game_results(self, game_session_id: str) -> Dict[str, Any]:
        """
        Get the results of a completed game.
        
        Args:
            game_session_id: ID of the game session
            
        Returns:
            Dictionary with game results
        """
        # Ensure game_session_id is a valid UUID string
        game_session_id = ensure_uuid(game_session_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")
        
        # Get all participants
        participants = await self.game_participant_repo.get_by_game_session_id(game_session_id)
        
        # Sort participants by score (descending)
        participants.sort(key=lambda p: p.score, reverse=True)
        
        # Get all game questions
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)
        
        # Prepare question results
        question_results = []
        for gq in game_questions:
            # Get the original question
            original_question = await self.question_repo.get_by_id(gq.question_id)
            if original_question:
                # Count correct answers
                correct_count = 0
                total_answered = 0
                
                for participant_id, answer in gq.participant_answers.items():
                    total_answered += 1
                    if answer.lower().strip() == original_question.answer.lower().strip():
                        correct_count += 1
                
                question_results.append({
                    "index": gq.question_index,
                    "question_text": original_question.question,
                    "correct_answer": original_question.answer,
                    "correct_count": correct_count,
                    "total_answered": total_answered,
                    "correct_percentage": (correct_count / total_answered * 100) if total_answered > 0 else 0
                })
        
        # Prepare participant results
        participant_results = [
            {
                "id": p.id,
                "user_id": p.user_id,
                "display_name": p.display_name,
                "score": p.score,
                "is_host": p.is_host
            }
            for p in participants
        ]
        
        return {
            "game_id": game_session_id,
            "game_code": game_session.code,
            "status": game_session.status,
            "participants": participant_results,
            "questions": question_results,
            "total_questions": len(game_questions),
            "completed_at": datetime.utcnow().isoformat()
        }
    
    async def cancel_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        """
        Cancel an active or pending game.
        
        Args:
            game_session_id: ID of the game session
            host_user_id: ID of the host user (for permission check)
            
        Returns:
            Updated GameSession object
            
        Raises:
            ValueError: If the game cannot be cancelled
        """
        # Ensure IDs are valid UUID strings
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        
        # Get the game session
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")
        
        # Verify the user is the host
        if game_session.host_user_id != host_user_id:
            raise ValueError("Only the host can cancel the game")
        
        # Check if the game is in a state that can be cancelled
        if game_session.status not in [GameStatus.PENDING, GameStatus.ACTIVE]:
            raise ValueError(f"Game cannot be cancelled (current status: {game_session.status})")
        
        # Update game status to cancelled
        updated_game = await self.game_session_repo.update_game_status(
            game_id=game_session_id,
            status=GameStatus.CANCELLED
        )
        
        logger.info(f"Game {game_session_id} cancelled by host {host_user_id}")
        
        return updated_game
    
    async def get_user_games(self, user_id: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        """
        Get all games a user is participating in.
        
        Args:
            user_id: ID of the user
            include_completed: Whether to include completed games
            
        Returns:
            List of dictionaries with game information
        """
        # Ensure user_id is a valid UUID string
        user_id = ensure_uuid(user_id)
        
        # Get all participations for this user
        participations = await self.game_participant_repo.get_user_active_games(user_id)
        
        results = []
        for participation in participations:
            # Get the game session
            game_session = await self.game_session_repo.get_by_id(participation.game_session_id)
            if not game_session:
                continue
                
            # Skip completed/cancelled games if not requested
            if not include_completed and game_session.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]:
                continue
                
            # Get all participants for this game
            participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
            
            # Create a simplified game record
            game_info = {
                "id": game_session.id,
                "code": game_session.code,
                "status": game_session.status,
                "participant_count": len(participants),
                "max_participants": game_session.max_participants,
                "current_question": game_session.current_question_index,
                "total_questions": game_session.question_count,
                "is_host": participation.is_host,
                "created_at": game_session.created_at.isoformat(),
                "updated_at": game_session.updated_at.isoformat()
            }
            
            results.append(game_info)
            
        return results