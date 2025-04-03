# backend/src/services/game_service.py
import random
import string
import logging
import asyncio
from typing import List, Optional, Tuple, Dict, Any, Set # Added Set
from datetime import datetime, timedelta, timezone

# Models
from ..models.game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from ..models.game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate
from ..models.question import Question
# --- ADD HISTORY MODELS ---
from ..models.user_question_history import UserQuestionHistoryCreate
# --- END HISTORY MODELS ---

# Repositories
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.user_repository import UserRepository
# --- ADD HISTORY REPOS ---
from ..repositories.user_question_history_repository import UserQuestionHistoryRepository
from ..repositories.user_pack_history_repository import UserPackHistoryRepository
# --- END HISTORY REPOS ---

# Utils
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class GameService:
    """
    Service for game management operations.
    Handles business logic related to creating, joining, and playing
    multiplayer trivia games, including question selection and history tracking.
    """

    # --- MODIFIED __init__ ---
    def __init__(
        self,
        game_session_repository: GameSessionRepository,
        game_participant_repository: GameParticipantRepository,
        game_question_repository: GameQuestionRepository,
        question_repository: QuestionRepository,
        incorrect_answers_repository: IncorrectAnswersRepository,
        user_repository: UserRepository,
        # --- ADD HISTORY REPOS ---
        user_question_history_repository: UserQuestionHistoryRepository,
        user_pack_history_repository: UserPackHistoryRepository
        # --- END HISTORY REPOS ---
    ):
        """
        Initialize the service with required repositories.
        """
        self.game_session_repo = game_session_repository
        self.game_participant_repo = game_participant_repository
        self.game_question_repo = game_question_repository
        self.question_repo = question_repository
        self.incorrect_answers_repo = incorrect_answers_repository
        self.user_repo = user_repository
        # --- ADD HISTORY REPOS ---
        self.user_question_history_repo = user_question_history_repository
        self.user_pack_history_repo = user_pack_history_repository
        # --- END HISTORY REPOS ---
    # --- END MODIFIED __init__ ---

    # create_game_session remains unchanged

    async def create_game_session(
        self,
        host_user_id: str,
        pack_id: str,
        max_participants: int = 10,
        question_count: int = 10,
        time_limit_seconds: int = 0
    ) -> GameSession:
        host_user_id = ensure_uuid(host_user_id)
        pack_id = ensure_uuid(pack_id)
        game_code = await self._generate_unique_game_code()
        game_session_data = GameSessionCreate(
            code=game_code, host_user_id=host_user_id, pack_id=pack_id,
            max_participants=max_participants, question_count=question_count,
            time_limit_seconds=time_limit_seconds, status=GameStatus.PENDING
        )
        game_session = await self.game_session_repo.create(obj_in=game_session_data)
        logger.info(f"Created game session with ID: {game_session.id}, code: {game_session.code}")
        host_display_name = "Captain"
        try:
            host_user = await self.user_repo.get_by_id(host_user_id)
            if host_user and host_user.displayname:
                host_display_name = host_user.displayname
            else: logger.warning(f"Could not find user or display name for host {host_user_id}. Using default '{host_display_name}'.")
        except Exception as e: logger.error(f"Error fetching host user {host_user_id} details: {e}. Using default name.")
        host_participant_data = GameParticipantCreate(
            game_session_id=game_session.id, user_id=host_user_id,
            display_name=host_display_name, is_host=True
        )
        await self.game_participant_repo.create(obj_in=host_participant_data)
        logger.info(f"Created host participant record for game {game_session.id} with name '{host_display_name}'")
        return game_session

    # _generate_unique_game_code remains unchanged
    async def _generate_unique_game_code(self, length: int = 6) -> str:
        characters = string.ascii_uppercase + string.digits
        characters = characters.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
        max_attempts = 10
        for _ in range(max_attempts):
            code = ''.join(random.choice(characters) for _ in range(length))
            existing_session = await self.game_session_repo.get_by_code(code)
            if not existing_session: return code
        logger.warning(f"Failed to generate unique code of length {length}, trying length {length+1}")
        return await self._generate_unique_game_code(length + 1)

    # join_game remains unchanged
    async def join_game(
        self,
        game_code: str,
        user_id: str,
        display_name: str
    ) -> Tuple[GameSession, GameParticipant]:
        user_id = ensure_uuid(user_id)
        game_session = await self.game_session_repo.get_by_code(game_code)
        if not game_session: raise ValueError(f"Game with code {game_code} not found")
        if game_session.status != GameStatus.PENDING: raise ValueError(f"Game is not accepting new players (status: {game_session.status})")
        participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
        if len(participants) >= game_session.max_participants: raise ValueError(f"Game with code {game_code} is full")
        existing_participant = await self.game_participant_repo.get_by_user_and_game(user_id, game_session.id)
        if existing_participant:
            logger.info(f"User {user_id} ({display_name}) rejoining game {game_code}")
            if existing_participant.display_name != display_name:
                logger.info(f"Updating display name for rejoining user {user_id} to '{display_name}'")
                updated_participant_record = await self.game_participant_repo.update(
                    id=existing_participant.id, obj_in=GameParticipantUpdate(display_name=display_name) # type: ignore[call-arg]
                )
                if updated_participant_record: return game_session, updated_participant_record
            return game_session, existing_participant
        participant_data = GameParticipantCreate(
            game_session_id=game_session.id, user_id=user_id,
            display_name=display_name, is_host=False
        )
        participant = await self.game_participant_repo.create(obj_in=participant_data)
        logger.info(f"User {user_id} ({display_name}) joined game {game_code} as participant {participant.id}")
        return game_session, participant

    # --- MODIFIED start_game ---
    async def start_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        """
        Start a game session: Select/prioritize questions based on user history,
        populate game_questions, update user_pack_history, and set game to active.

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

        # 1. Validation
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game with ID {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only the host can start the game")
        if game_session.status != GameStatus.PENDING: raise ValueError(f"Game cannot be started (current status: {game_session.status})")

        # 2. Get Participants
        participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
        participant_user_ids = [p.user_id for p in participants]
        if not participant_user_ids: raise ValueError("Cannot start a game with no participants")

        # 3. Select and Prepare Game Questions (using new helper method)
        selected_questions_for_game = await self._select_questions_for_game(
            pack_id=game_session.pack_id,
            target_count=game_session.question_count,
            participant_user_ids=participant_user_ids
        )

        actual_question_count = len(selected_questions_for_game)
        if actual_question_count == 0: raise ValueError("No questions available for this game pack.")

        # Adjust game session count if fewer questions were available
        if actual_question_count < game_session.question_count:
            logger.warning(
                f"Only {actual_question_count} questions available for game {game_session_id}, " +
                f"requested {game_session.question_count}. Updating game session."
            )
            updated_session = await self.game_session_repo.update(
                 id=game_session_id,
                 obj_in=GameSessionUpdate(question_count=actual_question_count) # type: ignore[call-arg]
            )
            if not updated_session: raise ValueError(f"Failed to update question count for game {game_session_id}")
            game_session = updated_session # Use the updated session object

        # 4. Populate `game_questions` Table Concurrently
        game_question_creation_tasks = []
        for index, question in enumerate(selected_questions_for_game):
            question_data = GameQuestionCreate(
                game_session_id=game_session_id,
                question_id=question.id,
                question_index=index
            )
            game_question_creation_tasks.append(
                asyncio.create_task(self.game_question_repo.create(obj_in=question_data))
            )
        game_question_results = await asyncio.gather(*game_question_creation_tasks, return_exceptions=True)
        # Check for errors during game_question creation
        failed_creations = [i for i, res in enumerate(game_question_results) if isinstance(res, Exception)]
        if failed_creations:
            logger.error(f"Failed to create {len(failed_creations)} game_question records for game {game_session_id}. Errors: {game_question_results}")
            # Decide on error handling: Maybe cancel game or proceed with fewer questions? For now, raise error.
            raise ValueError("Failed to prepare all game questions.")
        logger.info(f"Created {actual_question_count} game question records for game {game_session_id}")

        # 5. Update `user_pack_history` Concurrently
        pack_history_tasks = [
            asyncio.create_task(
                self.user_pack_history_repo.increment_play_count(user_id, game_session.pack_id)
            ) for user_id in participant_user_ids
        ]
        pack_history_results = await asyncio.gather(*pack_history_tasks, return_exceptions=True)
        # Log warnings for any failures but don't block game start
        failed_history_updates = [i for i, res in enumerate(pack_history_results) if isinstance(res, Exception) or res is None]
        if failed_history_updates:
            logger.warning(f"Failed to update pack history for {len(failed_history_updates)} users in game {game_session_id}.")

        # 6. Update Game Status
        updated_game = await self.game_session_repo.update(
            id=game_session_id,
            obj_in=GameSessionUpdate(
                status=GameStatus.ACTIVE,
                current_question_index=0,
                updated_at=datetime.now(timezone.utc)
            ) # type: ignore[call-arg]
        )
        if not updated_game: raise ValueError(f"Failed to update game status to ACTIVE for game {game_session_id}")

        logger.info(f"Game {game_session_id} started with {actual_question_count} questions by host {host_user_id}")
        return updated_game
    # --- END MODIFIED start_game ---

    # --- MODIFIED _select_questions_for_game ---
    async def _select_questions_for_game(
        self,
        pack_id: str,
        target_count: int,
        participant_user_ids: List[str]
    ) -> List[Question]:
        """
        Selects questions for a game, prioritizing unseen questions by participants.

        Args:
            pack_id: The ID of the pack to select questions from.
            target_count: The desired number of questions.
            participant_user_ids: List of user IDs participating in the game.

        Returns:
            A list of selected Question objects, shuffled.
        """
        pack_id_str = ensure_uuid(pack_id)

        # 1. Fetch all questions in the pack
        all_pack_questions = await self.question_repo.get_by_pack_id(pack_id_str)
        if not all_pack_questions:
            logger.warning(f"No questions found in pack {pack_id_str}")
            return []

        # Effective count cannot exceed available questions
        effective_count = min(target_count, len(all_pack_questions))
        if effective_count < target_count:
             logger.warning(f"Pack {pack_id_str} only has {len(all_pack_questions)} questions, requested {target_count}. Using {effective_count}.")

        pack_question_ids = [q.id for q in all_pack_questions]

        # 2. Fetch seen question IDs for the participants within this pack
        seen_question_ids = await self.user_question_history_repo.get_seen_question_ids_for_users(
            user_ids=participant_user_ids,
            question_ids=pack_question_ids
        )
        logger.info(f"Found {len(seen_question_ids)} previously seen questions by participants for pack {pack_id_str}.")

        # 3. Partition questions
        unseen_questions: List[Question] = []
        seen_questions: List[Question] = []
        for q in all_pack_questions:
            if q.id in seen_question_ids:
                seen_questions.append(q)
            else:
                unseen_questions.append(q)

        # 4. Select questions, prioritizing unseen
        selected_questions_for_game: List[Question] = []
        random.shuffle(unseen_questions) # Shuffle unseen questions
        num_needed = effective_count

        # Add from unseen pool first
        take_from_unseen = min(num_needed, len(unseen_questions))
        selected_questions_for_game.extend(unseen_questions[:take_from_unseen])
        num_needed -= take_from_unseen
        logger.info(f"Selected {take_from_unseen} unseen questions.")

        # If still need more, add from seen pool
        if num_needed > 0:
            logger.info(f"Needing {num_needed} more questions, selecting from seen pool ({len(seen_questions)} available).")
            random.shuffle(seen_questions) # Shuffle seen questions
            take_from_seen = min(num_needed, len(seen_questions))
            selected_questions_for_game.extend(seen_questions[:take_from_seen])
            num_needed -= take_from_seen

        # 5. Final shuffle of the selected list
        random.shuffle(selected_questions_for_game)

        logger.info(f"Final selected questions for game: {len(selected_questions_for_game)}")
        return selected_questions_for_game
    # --- END MODIFIED _select_questions_for_game ---


    # _advance_to_next_question remains unchanged
    async def _advance_to_next_question(
        self,
        game_session_id: str,
        next_index: Optional[int] = None
    ) -> Optional[GameQuestion]:
        # ... (implementation remains the same as before) ...
        game_session_id = ensure_uuid(game_session_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: logger.error(f"Game session {game_session_id} not found during advance"); return None
        if next_index is None: next_index = game_session.current_question_index + 1
        total_questions_in_game = game_session.question_count
        if next_index >= total_questions_in_game:
            if game_session.status == GameStatus.ACTIVE:
                updated_session = await self.game_session_repo.update_game_status(game_id=game_session_id, status=GameStatus.COMPLETED)
                if updated_session: logger.info(f"Game {game_session_id} completed")
                else: logger.error(f"Failed to update game status to COMPLETED for {game_session_id}")
            else: logger.info(f"Game {game_session_id} already in status {game_session.status}")
            return None
        updated_session = await self.game_session_repo.update(id=game_session_id, obj_in=GameSessionUpdate(current_question_index=next_index) )# type: ignore[call-arg]
        if not updated_session: logger.error(f"Failed to update current_question_index for game {game_session_id}"); return None
        next_game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id=game_session_id, question_index=next_index)
        if next_game_question:
            started_question = await self.game_question_repo.start_question(next_game_question.id)
            if started_question: logger.info(f"Game {game_session_id} advanced to question {next_index}"); return started_question
            else: logger.error(f"Failed to mark game question {next_game_question.id} as started for game {game_session_id}"); return None
        else: logger.error(f"Game {game_session_id}: Failed to find game question at index {next_index}"); return None

    # --- MODIFIED submit_answer ---
    async def submit_answer(
        self,
        game_session_id: str,
        participant_id: str,
        question_index: int,
        answer: str
    ) -> Dict[str, Any]:
        """
        Process a participant's submitted answer, calculate score, and update history.
        """
        game_session_id = ensure_uuid(game_session_id)
        participant_id = ensure_uuid(participant_id)

        # 1. Validation & Fetch Data
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game not active")

        participant = await self.game_participant_repo.get_by_id(participant_id)
        if not participant or participant.game_session_id != game_session_id: raise ValueError(f"Participant not found in game")

        game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id, question_index)
        if not game_question: raise ValueError(f"Question index {question_index} not found")
        if game_session.current_question_index != question_index: raise ValueError(f"Not the current question")
        if not game_question.start_time: raise ValueError(f"Question not started")
        if game_question.end_time: raise ValueError(f"Question ended")
        if participant_id in game_question.participant_answers: raise ValueError("Answer already submitted")

        # Record answer in GameQuestion first
        await self.game_question_repo.record_participant_answer(game_question.id, participant_id, answer)

        # 2. Check Correctness & Score
        original_question = await self.question_repo.get_by_id(game_question.question_id)
        if not original_question:
            logger.error(f"Original question {game_question.question_id} not found for score calculation")
            return {"success": False, "error": "Original question data missing"}

        is_correct = answer.lower().strip() == original_question.answer.lower().strip()
        score = 0
        if is_correct:
            # Scoring logic (same as before)
            max_score = 1000
            now = datetime.now(timezone.utc)
            start_time = game_question.start_time
            if start_time:
                 if start_time.tzinfo is None: start_time = start_time.replace(tzinfo=timezone.utc)
                 try:
                     seconds_taken = (now - start_time).total_seconds()
                     time_limit = max(game_session.time_limit_seconds, 1) # Avoid division by zero
                     time_factor = max(0, 1 - (seconds_taken / time_limit))
                     score = int(max_score * time_factor)
                     score = max(score, 100) # Minimum score for correct answer
                 except Exception as e: logger.error(f"Time calculation error: {e}"); score = 100
            else: logger.warning("Start time missing"); score = 100

        # 3. Update Scores (GameQuestion and Participant Total)
        await self.game_question_repo.record_participant_score(game_question.id, participant_id, score)
        new_total_score = participant.score + score
        updated_participant = await self.game_participant_repo.update_score(participant_id, new_total_score)
        final_total_score = updated_participant.score if updated_participant else new_total_score

        # --- 4. Update User Question History ---
        try:
            history_data = UserQuestionHistoryCreate(
                user_id=participant.user_id,
                question_id=game_question.question_id,
                correct=is_correct
                # incorrect_answer_selected not directly tracked here easily, could be added if needed
            )
            await self.user_question_history_repo.create(obj_in=history_data)
            logger.debug(f"Recorded question history for user {participant.user_id}, question {game_question.question_id}")
        except Exception as hist_error:
            # Log error but don't fail the whole request
            logger.error(f"Failed to record question history for user {participant.user_id}, question {game_question.question_id}: {hist_error}", exc_info=True)
        # --- END History Update ---

        return {
            "success": True, "is_correct": is_correct,
            "correct_answer": original_question.answer, "score": score,
            "total_score": final_total_score
        }
    # --- END MODIFIED submit_answer ---

    # end_current_question remains unchanged
    async def end_current_question(
        self,
        game_session_id: str,
        host_user_id: str
    ) -> Dict[str, Any]:
        # ... (implementation remains the same as before) ...
        game_session_id = ensure_uuid(game_session_id); host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id);
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only host can end question")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game not active")
        current_index = game_session.current_question_index
        current_game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id, current_index)
        if current_game_question and current_game_question.start_time and not current_game_question.end_time:
             await self.game_question_repo.end_question(current_game_question.id)
        elif current_game_question and current_game_question.end_time: logger.info(f"Question {current_index} already ended.")
        elif not current_game_question: logger.warning(f"Current game question (index {current_index}) not found.")
        next_game_question = await self._advance_to_next_question(game_session_id)
        if next_game_question:
             original_question = await self.question_repo.get_by_id(next_game_question.question_id)
             if not original_question: return {"game_complete": False, "error": "Failed to load next question data"}
             incorrect_answers = await self.incorrect_answers_repo.get_by_question_id(next_game_question.question_id)
             incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []
             all_options = [original_question.answer] + incorrect_options; random.shuffle(all_options)
             updated_game_session = await self.game_session_repo.get_by_id(game_session_id)
             time_limit = updated_game_session.time_limit_seconds if updated_game_session else game_session.time_limit_seconds
             return {"game_complete": False, "next_question": {"index": next_game_question.question_index, "question_text": original_question.question, "options": all_options, "time_limit": time_limit}}
        else:
             logger.info(f"Advancing returned None. Game {game_session_id} should be complete.")
             final_game_session = await self.game_session_repo.get_by_id(game_session_id)
             if final_game_session and final_game_session.status == GameStatus.COMPLETED:
                 final_results = await self.get_game_results(game_session_id)
                 return {"game_complete": True, "results": final_results}
             else:
                 logger.warning(f"Game {game_session_id} advance returned None, but status is {final_game_session.status if final_game_session else 'Not Found'}.")
                 return {"game_complete": True, "results": None}

    # get_game_participants remains unchanged
    async def get_game_participants(self, game_session_id: str) -> List[Dict[str, Any]]:
        # ... (implementation remains the same as before) ...
        game_session_id_str = ensure_uuid(game_session_id)
        participants: List[GameParticipant] = await self.game_participant_repo.get_by_game_session_id(game_session_id_str)
        return [{"id": p.id, "user_id": p.user_id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]

    # get_game_results remains unchanged
    async def get_game_results(self, game_session_id: str) -> Dict[str, Any]:
        # ... (implementation remains the same as before) ...
        game_session_id = ensure_uuid(game_session_id); game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.status != GameStatus.COMPLETED: logger.warning(f"Requesting results for non-completed game {game_session_id}")
        participants = await self.game_participant_repo.get_by_game_session_id(game_session_id); participants.sort(key=lambda p: p.score, reverse=True)
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)
        question_results = []
        for gq in game_questions:
             original_question = await self.question_repo.get_by_id(gq.question_id)
             if original_question:
                 correct_count = sum(1 for score in gq.participant_scores.values() if score > 0)
                 total_answered = len(gq.participant_answers)
                 correct_percentage = (correct_count / total_answered * 100) if total_answered > 0 else 0
                 question_results.append({"index": gq.question_index, "question_text": original_question.question, "correct_answer": original_question.answer, "correct_count": correct_count, "total_answered": total_answered, "correct_percentage": correct_percentage})
        participant_results = [{"id": p.id, "user_id": p.user_id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]
        completion_time = game_session.updated_at if game_session.status == GameStatus.COMPLETED else datetime.now(timezone.utc)
        return {"game_id": game_session_id, "game_code": game_session.code, "status": game_session.status, "participants": participant_results, "questions": question_results, "total_questions": len(game_questions), "completed_at": completion_time}

    # cancel_game remains unchanged
    async def cancel_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        # ... (implementation remains the same as before) ...
        game_session_id = ensure_uuid(game_session_id); host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only host can cancel")
        if game_session.status not in [GameStatus.PENDING, GameStatus.ACTIVE]: raise ValueError(f"Game cannot be cancelled (status: {game_session.status})")
        updated_game = await self.game_session_repo.update_game_status(game_id=game_session_id, status=GameStatus.CANCELLED)
        if not updated_game: raise ValueError(f"Failed to cancel game {game_session_id}")
        logger.info(f"Game {game_session_id} cancelled by host {host_user_id}")
        return updated_game

    # get_user_games remains unchanged
    async def get_user_games(self, user_id: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        # ... (implementation remains the same as before) ...
        user_id = ensure_uuid(user_id); participations = await self.game_participant_repo.get_user_active_games(user_id)
        results = []; processed_game_ids = set()
        for participation in participations:
             game_session_id = participation.game_session_id
             if game_session_id in processed_game_ids: continue
             game_session = await self.game_session_repo.get_by_id(game_session_id)
             if not game_session: logger.warning(f"Game session {game_session_id} not found for participation {participation.id}"); continue
             if not include_completed and game_session.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]: continue
             participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
             game_info = {"id": game_session.id, "code": game_session.code, "status": game_session.status, "participant_count": len(participants), "max_participants": game_session.max_participants, "current_question": game_session.current_question_index, "total_questions": game_session.question_count, "is_host": participation.is_host, "created_at": game_session.created_at, "updated_at": game_session.updated_at}
             results.append(game_info); processed_game_ids.add(game_session_id)
        return results