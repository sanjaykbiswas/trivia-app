# backend/src/services/game_service.py
import random
import string
import logging
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone

from ..models.game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from ..models.game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
# --- ADD UserRepository IMPORT ---
from ..repositories.user_repository import UserRepository
# --- END ADD UserRepository IMPORT ---
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

    # --- MODIFIED __init__ ---
    def __init__(
        self,
        game_session_repository: GameSessionRepository,
        game_participant_repository: GameParticipantRepository,
        game_question_repository: GameQuestionRepository,
        question_repository: QuestionRepository,
        incorrect_answers_repository: IncorrectAnswersRepository,
        user_repository: UserRepository # <<< ADDED Dependency
    ):
        """
        Initialize the service with required repositories.

        Args:
            game_session_repository: Repository for game session operations
            game_participant_repository: Repository for game participant operations
            game_question_repository: Repository for game question operations
            question_repository: Repository for question operations
            incorrect_answers_repository: Repository for incorrect answers operations
            user_repository: Repository for user operations (needed for host name) # <<< ADDED Arg Doc
        """
        self.game_session_repo = game_session_repository
        self.game_participant_repo = game_participant_repository
        self.game_question_repo = game_question_repository
        self.question_repo = question_repository
        self.incorrect_answers_repo = incorrect_answers_repository
        self.user_repo = user_repository # <<< ADDED Assignment
    # --- END MODIFIED __init__ ---

    # --- MODIFIED create_game_session ---
    async def create_game_session(
        self,
        host_user_id: str,
        pack_id: str,
        max_participants: int = 10,
        question_count: int = 10,
        time_limit_seconds: int = 0
    ) -> GameSession:
        """
        Create a new game session. Fetches host display name.

        Args:
            host_user_id: ID of the user creating the game
            pack_id: ID of the question pack to use
            max_participants: Maximum number of participants allowed
            question_count: Number of questions to include
            time_limit_seconds: Time limit per question (0 for no limit)

        Returns:
            Created GameSession object
        """
        host_user_id = ensure_uuid(host_user_id)
        pack_id = ensure_uuid(pack_id)

        game_code = await self._generate_unique_game_code()

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

        # --- *** FETCH HOST NAME *** ---
        host_display_name = "Captain" # Default fallback
        try:
            host_user = await self.user_repo.get_by_id(host_user_id)
            if host_user and host_user.displayname:
                host_display_name = host_user.displayname
                logger.info(f"Fetched display name '{host_display_name}' for host user {host_user_id}")
            else:
                logger.warning(f"Could not find user or display name for host {host_user_id}. Using default '{host_display_name}'.")
        except Exception as e:
             logger.error(f"Error fetching host user {host_user_id} details: {e}. Using default name.")
        # --- *** END FETCH HOST NAME *** ---

        host_participant_data = GameParticipantCreate(
            game_session_id=game_session.id,
            user_id=host_user_id,
            # --- *** USE FETCHED/DEFAULT NAME *** ---
            display_name=host_display_name,
            # --- *** END NAME USAGE *** ---
            is_host=True
        )
        await self.game_participant_repo.create(obj_in=host_participant_data)
        logger.info(f"Created host participant record for game {game_session.id} with name '{host_display_name}'")

        return game_session
    # --- END MODIFIED create_game_session ---

    async def _generate_unique_game_code(self, length: int = 6) -> str:
        """
        Generate a unique, easy-to-read game code.

        Args:
            length: Length of the code to generate

        Returns:
            Unique game code string
        """
        characters = string.ascii_uppercase + string.digits
        # Remove visually similar characters
        characters = characters.replace('O', '').replace('0', '').replace('I', '').replace('1', '')

        max_attempts = 10
        for _ in range(max_attempts):
            code = ''.join(random.choice(characters) for _ in range(length))
            existing_session = await self.game_session_repo.get_by_code(code)
            if not existing_session:
                return code
        # If we fail after many attempts, try a longer code (rare case)
        logger.warning(f"Failed to generate unique code of length {length}, trying length {length+1}")
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
        user_id = ensure_uuid(user_id)
        game_session = await self.game_session_repo.get_by_code(game_code)
        if not game_session:
            raise ValueError(f"Game with code {game_code} not found")

        if game_session.status != GameStatus.PENDING:
            raise ValueError(f"Game is not accepting new players (status: {game_session.status})")

        participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
        if len(participants) >= game_session.max_participants:
            raise ValueError(f"Game with code {game_code} is full")

        # Check if this user is already a participant
        existing_participant = await self.game_participant_repo.get_by_user_and_game(user_id, game_session.id)
        if existing_participant:
            logger.info(f"User {user_id} ({display_name}) rejoining game {game_code}")
            # Optionally update display name or last activity? For now, just return existing.
            # If name changed, we should update it here.
            if existing_participant.display_name != display_name:
                logger.info(f"Updating display name for rejoining user {user_id} to '{display_name}'")
                updated_participant_record = await self.game_participant_repo.update(
                    id=existing_participant.id,
                    obj_in=GameParticipantUpdate(display_name=display_name)
                )
                if updated_participant_record:
                     return game_session, updated_participant_record

            return game_session, existing_participant

        # Create new participant record
        participant_data = GameParticipantCreate(
            game_session_id=game_session.id,
            user_id=user_id,
            display_name=display_name,
            is_host=False # Joining player is never the host
        )

        participant = await self.game_participant_repo.create(obj_in=participant_data)
        logger.info(f"User {user_id} ({display_name}) joined game {game_code} as participant {participant.id}")

        return game_session, participant

    async def start_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        """
        Start a game session. Ensures questions are created before activation.

        Args:
            game_session_id: ID of the game to start
            host_user_id: ID of the user trying to start the game (must be host)

        Returns:
            Updated GameSession object

        Raises:
            ValueError: If the game cannot be started
        """
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            raise ValueError(f"Game with ID {game_session_id} not found")

        if game_session.host_user_id != host_user_id:
            raise ValueError("Only the host can start the game")

        if game_session.status != GameStatus.PENDING:
            raise ValueError(f"Game cannot be started (current status: {game_session.status})")

        # Select and Create Game Questions FIRST
        questions = await self._select_questions_for_game(
            pack_id=game_session.pack_id,
            count=game_session.question_count
        )

        actual_question_count = len(questions)
        if actual_question_count == 0:
            raise ValueError("No questions available for this game pack.")

        if actual_question_count < game_session.question_count:
            logger.warning(
                f"Only {actual_question_count} questions available for game {game_session_id}, " +
                f"requested {game_session.question_count}. Using available questions."
            )
            game_session = await self.game_session_repo.update(
                 id=game_session_id,
                 obj_in=GameSessionUpdate(question_count=actual_question_count)
             )
            if not game_session:
                raise ValueError(f"Failed to update question count for game {game_session_id}")

        game_question_creation_tasks = []
        for index, question in enumerate(questions):
            question_data = GameQuestionCreate(
                game_session_id=game_session_id,
                question_id=question.id,
                question_index=index
            )
            game_question_creation_tasks.append(
                asyncio.create_task(self.game_question_repo.create(obj_in=question_data))
            )
        await asyncio.gather(*game_question_creation_tasks)
        logger.info(f"Created {len(questions)} game question records for game {game_session_id}")

        # Update game status and current index
        updated_game = await self.game_session_repo.update(
            id=game_session_id,
            obj_in=GameSessionUpdate(
                status=GameStatus.ACTIVE,
                current_question_index=0,
                updated_at=datetime.now(timezone.utc)
            )
        )
        if not updated_game:
             raise ValueError(f"Failed to update game status to ACTIVE for game {game_session_id}")

        logger.info(f"Game {game_session_id} started with {len(questions)} questions by host {host_user_id}")
        return updated_game

    async def _select_questions_for_game(
        self,
        pack_id: str,
        count: int
    ) -> List[Question]:
        pack_id = ensure_uuid(pack_id)
        all_questions = await self.question_repo.get_by_pack_id(pack_id)
        if not all_questions:
             logger.warning(f"No questions found in pack {pack_id}")
             return []
        if len(all_questions) <= count:
            logger.info(f"Using all {len(all_questions)} available questions for game.")
            random.shuffle(all_questions)
            return all_questions
        logger.info(f"Selecting {count} random questions from {len(all_questions)} available.")
        return random.sample(all_questions, count)

    async def _advance_to_next_question(
        self,
        game_session_id: str,
        next_index: Optional[int] = None
    ) -> Optional[GameQuestion]:
        game_session_id = ensure_uuid(game_session_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session:
            logger.error(f"Game session {game_session_id} not found during advance")
            return None
        if next_index is None:
            next_index = game_session.current_question_index + 1
        total_questions_in_game = game_session.question_count
        if next_index >= total_questions_in_game:
            if game_session.status == GameStatus.ACTIVE:
                updated_session = await self.game_session_repo.update_game_status(
                    game_id=game_session_id,
                    status=GameStatus.COMPLETED
                )
                if updated_session: logger.info(f"Game {game_session_id} completed")
                else: logger.error(f"Failed to update game status to COMPLETED for {game_session_id}")
            else: logger.info(f"Game {game_session_id} already in status {game_session.status}")
            return None
        updated_session = await self.game_session_repo.update(
            id=game_session_id,
            obj_in=GameSessionUpdate(current_question_index=next_index)
        )
        if not updated_session:
             logger.error(f"Failed to update current_question_index for game {game_session_id}")
             return None
        next_game_question = await self.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_session_id,
            question_index=next_index
        )
        if next_game_question:
            started_question = await self.game_question_repo.start_question(next_game_question.id)
            if started_question:
                logger.info(f"Game {game_session_id} advanced to question {next_index}")
                return started_question
            else:
                 logger.error(f"Failed to mark game question {next_game_question.id} as started for game {game_session_id}")
                 return None
        else:
             logger.error(f"Game {game_session_id}: Failed to find game question at index {next_index}")
             return None

    async def submit_answer(
        self,
        game_session_id: str,
        participant_id: str,
        question_index: int,
        answer: str
    ) -> Dict[str, Any]:
        game_session_id = ensure_uuid(game_session_id)
        participant_id = ensure_uuid(participant_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game with ID {game_session_id} not found")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game is not active (status: {game_session.status})")
        participant = await self.game_participant_repo.get_by_id(participant_id)
        if not participant or participant.game_session_id != game_session_id: raise ValueError(f"Participant {participant_id} not found in game {game_session_id}")
        game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id=game_session_id, question_index=question_index)
        if not game_question: raise ValueError(f"Question index {question_index} not found in game {game_session_id}")
        if game_session.current_question_index != question_index: raise ValueError(f"Cannot answer question {question_index}, current question is {game_session.current_question_index}")
        if not game_question.start_time: raise ValueError(f"Question {question_index} has not started yet")
        if game_question.end_time: raise ValueError(f"Question {question_index} has already ended")
        if participant_id in game_question.participant_answers: raise ValueError("Answer already submitted for this question")

        await self.game_question_repo.record_participant_answer(question_id=game_question.id, participant_id=participant_id, answer=answer)
        original_question = await self.question_repo.get_by_id(game_question.question_id)
        if not original_question:
            logger.error(f"Original question {game_question.question_id} not found")
            return {"success": False, "is_correct": False, "correct_answer": "N/A", "score": 0, "total_score": participant.score, "error": "Original question data missing"}

        is_correct = answer.lower().strip() == original_question.answer.lower().strip()
        score = 0
        if is_correct:
            max_score = 1000
            now = datetime.now(timezone.utc)
            start_time = game_question.start_time
            if start_time:
                if start_time.tzinfo is None:
                     logger.warning(f"Game question {game_question.id} start_time is timezone-naive. Assuming UTC.")
                     start_time = start_time.replace(tzinfo=timezone.utc)
                try:
                     seconds_taken = (now - start_time).total_seconds()
                     time_limit = max(game_session.time_limit_seconds, 1)
                     time_factor = max(0, 1 - (seconds_taken / time_limit))
                     score = int(max_score * time_factor)
                     score = max(score, 100)
                except (TypeError, ValueError) as e:
                     logger.error(f"Time calculation error for score: {e}. Granting base score.")
                     score = 100
            else:
                logger.warning(f"Question {question_index} start time not set. Granting base score.")
                score = 100

        await self.game_question_repo.record_participant_score(question_id=game_question.id, participant_id=participant_id, score=score)
        new_total_score = participant.score + score
        updated_participant = await self.game_participant_repo.update_score(participant_id=participant_id, new_score=new_total_score)
        final_total_score = updated_participant.score if updated_participant else new_total_score

        return {"success": True, "is_correct": is_correct, "correct_answer": original_question.answer, "score": score, "total_score": final_total_score}

    async def end_current_question(
        self,
        game_session_id: str,
        host_user_id: str
    ) -> Dict[str, Any]:
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game with ID {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only the host can end the current question")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game is not active (status: {game_session.status})")

        current_index = game_session.current_question_index
        current_game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id=game_session_id, question_index=current_index)
        if current_game_question and current_game_question.start_time and not current_game_question.end_time:
            await self.game_question_repo.end_question(current_game_question.id)
        elif current_game_question and current_game_question.end_time: logger.info(f"Question {current_index} already ended.")
        elif not current_game_question: logger.warning(f"Current game question (index {current_index}) not found when trying to end.")

        next_game_question = await self._advance_to_next_question(game_session_id)
        if next_game_question:
            original_question = await self.question_repo.get_by_id(next_game_question.question_id)
            if not original_question: return {"game_complete": False, "error": "Failed to load next question data"}
            incorrect_answers = await self.incorrect_answers_repo.get_by_question_id(next_game_question.question_id)
            incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []
            all_options = [original_question.answer] + incorrect_options
            random.shuffle(all_options)
            updated_game_session = await self.game_session_repo.get_by_id(game_session_id)
            time_limit = updated_game_session.time_limit_seconds if updated_game_session else game_session.time_limit_seconds
            return {"game_complete": False, "next_question": {"index": next_game_question.question_index, "question_text": original_question.question, "options": all_options, "time_limit": time_limit}}
        else:
            logger.info(f"Advancing returned None. Game {game_session_id} should be complete. Checking status...")
            final_game_session = await self.game_session_repo.get_by_id(game_session_id)
            if final_game_session and final_game_session.status == GameStatus.COMPLETED:
                logger.info(f"Game status confirmed as COMPLETED. Fetching final results.")
                final_results = await self.get_game_results(game_session_id)
                return {"game_complete": True, "results": final_results}
            else:
                logger.warning(f"Game {game_session_id} advance returned None, but status is not COMPLETED (status: {final_game_session.status if final_game_session else 'Not Found'}). Returning completion flag without results.")
                return {"game_complete": True, "results": None}

    async def get_game_participants(self, game_session_id: str) -> List[Dict[str, Any]]:
        game_session_id_str = ensure_uuid(game_session_id)
        participants = await self.game_participant_repo.get_by_game_session_id(game_session_id_str)
        return [{"id": p.id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]

    async def get_game_results(self, game_session_id: str) -> Dict[str, Any]:
        game_session_id = ensure_uuid(game_session_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game with ID {game_session_id} not found")
        if game_session.status != GameStatus.COMPLETED: logger.warning(f"Requesting results for game {game_session_id} which is not completed (status: {game_session.status})")

        participants = await self.game_participant_repo.get_by_game_session_id(game_session_id)
        participants.sort(key=lambda p: p.score, reverse=True)
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)

        question_results = []
        for gq in game_questions:
            original_question = await self.question_repo.get_by_id(gq.question_id)
            if original_question:
                correct_count = sum(1 for pid, score in gq.participant_scores.items() if score > 0)
                total_answered = len(gq.participant_answers)
                question_results.append({"index": gq.question_index, "question_text": original_question.question, "correct_answer": original_question.answer, "correct_count": correct_count, "total_answered": total_answered, "correct_percentage": (correct_count / total_answered * 100) if total_answered > 0 else 0})

        participant_results = [{"id": p.id, "user_id": p.user_id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]
        completion_time = game_session.updated_at if game_session.status == GameStatus.COMPLETED else datetime.now(timezone.utc)
        return {"game_id": game_session_id, "game_code": game_session.code, "status": game_session.status, "participants": participant_results, "questions": question_results, "total_questions": len(game_questions), "completed_at": completion_time}

    async def cancel_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        game_session_id = ensure_uuid(game_session_id)
        host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game with ID {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only the host can cancel the game")
        if game_session.status not in [GameStatus.PENDING, GameStatus.ACTIVE]: raise ValueError(f"Game cannot be cancelled (current status: {game_session.status})")
        updated_game = await self.game_session_repo.update_game_status(game_id=game_session_id, status=GameStatus.CANCELLED)
        if not updated_game: raise ValueError(f"Failed to cancel game {game_session_id}")
        logger.info(f"Game {game_session_id} cancelled by host {host_user_id}")
        return updated_game

    async def get_user_games(self, user_id: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        user_id = ensure_uuid(user_id)
        participations = await self.game_participant_repo.get_user_active_games(user_id)
        results = []
        processed_game_ids = set()
        for participation in participations:
            game_session_id = participation.game_session_id
            if game_session_id in processed_game_ids: continue
            game_session = await self.game_session_repo.get_by_id(game_session_id)
            if not game_session:
                logger.warning(f"Game session {game_session_id} not found for participation {participation.id}")
                continue
            if not include_completed and game_session.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]: continue
            participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
            game_info = {"id": game_session.id, "code": game_session.code, "status": game_session.status, "participant_count": len(participants), "max_participants": game_session.max_participants, "current_question": game_session.current_question_index, "total_questions": game_session.question_count, "is_host": participation.is_host, "created_at": game_session.created_at, "updated_at": game_session.updated_at}
            results.append(game_info)
            processed_game_ids.add(game_session_id)
        return results