# backend/src/services/game_service.py
import random
import string
import logging
import asyncio
from typing import List, Optional, Tuple, Dict, Any, Set
from datetime import datetime, timedelta, timezone

# Models
from ..models.game_session import GameSession, GameSessionCreate, GameSessionUpdate, GameStatus
from ..models.game_participant import GameParticipant, GameParticipantCreate, GameParticipantUpdate
from ..models.game_question import GameQuestion, GameQuestionCreate, GameQuestionUpdate
from ..models.question import Question
from ..models.user_question_history import UserQuestionHistoryCreate

# Repositories
from ..repositories.game_session_repository import GameSessionRepository
from ..repositories.game_participant_repository import GameParticipantRepository
from ..repositories.game_question_repository import GameQuestionRepository
from ..repositories.question_repository import QuestionRepository
from ..repositories.incorrect_answers_repository import IncorrectAnswersRepository
from ..repositories.user_repository import UserRepository
from ..repositories.user_question_history_repository import UserQuestionHistoryRepository
from ..repositories.user_pack_history_repository import UserPackHistoryRepository

# Utils & Schemas
from ..utils import ensure_uuid
from ..api.schemas.game import GamePlayQuestionResponse

# --- WebSocket Integration ---
from ..websocket_manager import ConnectionManager
# --- End WebSocket Integration ---

# Configure logger
logger = logging.getLogger(__name__)

class GameService:
    """
    Service for game management operations.
    Handles business logic related to creating, joining, and playing
    multiplayer trivia games, including question selection, history tracking,
    and real-time updates via WebSockets.
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
        user_question_history_repository: UserQuestionHistoryRepository,
        user_pack_history_repository: UserPackHistoryRepository,
        connection_manager: ConnectionManager # <<< ADDED
    ):
        """
        Initialize the service with required repositories and connection manager.
        """
        self.game_session_repo = game_session_repository
        self.game_participant_repo = game_participant_repository
        self.game_question_repo = game_question_repository
        self.question_repo = question_repository
        self.incorrect_answers_repo = incorrect_answers_repository
        self.user_repo = user_repository
        self.user_question_history_repo = user_question_history_repository
        self.user_pack_history_repo = user_pack_history_repository
        self.connection_manager = connection_manager # <<< ADDED
    # --- END MODIFIED __init__ ---

    # create_game_session remains unchanged in its core logic,
    # but the host joining implicitly adds them to the room via WebSocket connect.
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
        # Note: Host will connect via WebSocket separately
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

    # --- MODIFIED join_game ---
    async def join_game(
        self,
        game_code: str,
        user_id: str,
        display_name: str
    ) -> Tuple[GameSession, GameParticipant]:
        user_id_str = ensure_uuid(user_id)
        game_session = await self.game_session_repo.get_by_code(game_code)
        if not game_session: raise ValueError(f"Game with code {game_code} not found")
        if game_session.status != GameStatus.PENDING: raise ValueError(f"Game is not accepting new players (status: {game_session.status})")

        participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
        if len(participants) >= game_session.max_participants: raise ValueError(f"Game with code {game_code} is full")

        existing_participant = await self.game_participant_repo.get_by_user_and_game(user_id_str, game_session.id)
        participant_record: GameParticipant
        is_rejoin = False

        if existing_participant:
            logger.info(f"User {user_id_str} ({display_name}) rejoining game {game_code}")
            is_rejoin = True
            if existing_participant.display_name != display_name:
                logger.info(f"Updating display name for rejoining user {user_id_str} to '{display_name}'")
                updated_record = await self.game_participant_repo.update(
                    id=existing_participant.id,
                    obj_in=GameParticipantUpdate(display_name=display_name) # type: ignore[call-arg]
                )
                if updated_record:
                     participant_record = updated_record
                     # Broadcast name change on rejoin if needed (UserService also handles updates)
                     await self._broadcast_participant_update(game_session.id, participant_record)
                else:
                     participant_record = existing_participant # Fallback if update fails
            else:
                 participant_record = existing_participant
        else:
            # New participant
            participant_data = GameParticipantCreate(
                game_session_id=game_session.id, user_id=user_id_str,
                display_name=display_name, is_host=False
            )
            participant_record = await self.game_participant_repo.create(obj_in=participant_data)
            logger.info(f"User {user_id_str} ({display_name}) joined game {game_code} as participant {participant_record.id}")

        # --- Broadcast Join Event ---
        if not is_rejoin: # Only broadcast for new joins here
             await self._broadcast_participant_update(game_session.id, participant_record)

        return game_session, participant_record
    # --- END MODIFIED join_game ---

    # --- Helper to broadcast participant updates ---
    async def _broadcast_participant_update(self, game_id: str, participant: GameParticipant):
        """Helper to format and broadcast participant join/update messages."""
        message = {
            "type": "participant_update",
            "payload": {
                "id": participant.id,
                "user_id": participant.user_id,
                "display_name": participant.display_name,
                "score": participant.score,
                "is_host": participant.is_host,
            }
        }
        await self.connection_manager.broadcast(message, game_id)
        logger.debug(f"Broadcasted participant update for user {participant.user_id} in game {game_id}")
    # --- End Helper ---

    # --- MODIFIED start_game ---
    async def start_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        """
        Start a game session: Select/prioritize questions based on user history,
        populate game_questions, update user_pack_history, set game to active,
        and broadcast the start event.
        """
        # ... (Validation and Question Selection logic remains the same as before) ...
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

        # 3. Select and Prepare Game Questions
        selected_questions_for_game = await self._select_questions_for_game(
            pack_id=game_session.pack_id,
            target_count=game_session.question_count,
            participant_user_ids=participant_user_ids
        )
        actual_question_count = len(selected_questions_for_game)
        if actual_question_count == 0: raise ValueError("No questions available for this game pack.")

        # Adjust game session count if needed
        if actual_question_count < game_session.question_count:
            updated_session = await self.game_session_repo.update(
                 id=game_session_id,
                 obj_in=GameSessionUpdate(question_count=actual_question_count) # type: ignore[call-arg]
            )
            if not updated_session: raise ValueError(f"Failed to update question count for game {game_session_id}")
            game_session = updated_session

        # 4. Populate `game_questions` Table Concurrently
        game_question_creation_tasks = [
            asyncio.create_task(self.game_question_repo.create(obj_in=GameQuestionCreate(
                game_session_id=game_session_id, question_id=q.id, question_index=idx
            ))) for idx, q in enumerate(selected_questions_for_game)
        ]
        game_question_results = await asyncio.gather(*game_question_creation_tasks, return_exceptions=True)
        failed_creations = [i for i, res in enumerate(game_question_results) if isinstance(res, Exception)]
        if failed_creations:
            logger.error(f"Failed to create {len(failed_creations)} game_question records for game {game_session_id}. Errors: {game_question_results}")
            raise ValueError("Failed to prepare all game questions.")
        logger.info(f"Created {actual_question_count} game question records for game {game_session_id}")

        # 5. Update `user_pack_history` Concurrently
        pack_history_tasks = [
            asyncio.create_task(self.user_pack_history_repo.increment_play_count(user_id, game_session.pack_id))
            for user_id in participant_user_ids
        ]
        pack_history_results = await asyncio.gather(*pack_history_tasks, return_exceptions=True)
        failed_history_updates = [i for i, res in enumerate(pack_history_results) if isinstance(res, Exception) or res is None]
        if failed_history_updates: logger.warning(f"Failed to update pack history for {len(failed_history_updates)} users in game {game_session_id}.")

        # 6. Update Game Status
        updated_game = await self.game_session_repo.update(
            id=game_session_id,
            obj_in=GameSessionUpdate(status=GameStatus.ACTIVE, current_question_index=0, updated_at=datetime.now(timezone.utc)) # type: ignore[call-arg]
        )
        if not updated_game: raise ValueError(f"Failed to update game status to ACTIVE for game {game_session_id}")

        # --- 7. Broadcast Game Started Event ---
        # Send game details and possibly the first question
        # Fetch the formatted first question for the broadcast
        play_questions = await self.get_questions_for_play(updated_game.id) # Use updated game ID
        first_question_payload = play_questions[0] if play_questions else None

        start_message = {
            "type": "game_started",
            "payload": {
                "game_id": updated_game.id,
                "status": updated_game.status.value,
                "total_questions": updated_game.question_count,
                "time_limit": updated_game.time_limit_seconds,
                "pack_id": updated_game.pack_id,
                # Include first question details directly in the start message
                "current_question": first_question_payload
            }
        }
        await self.connection_manager.broadcast(start_message, updated_game.id)
        logger.info(f"Broadcasted game_started event for game {updated_game.id}")
        # --- End Broadcast ---

        logger.info(f"Game {game_session_id} started with {actual_question_count} questions by host {host_user_id}")
        return updated_game
    # --- END MODIFIED start_game ---

    # _select_questions_for_game remains unchanged
    async def _select_questions_for_game(
        self,
        pack_id: str,
        target_count: int,
        participant_user_ids: List[str]
    ) -> List[Question]:
        pack_id_str = ensure_uuid(pack_id)
        all_pack_questions = await self.question_repo.get_by_pack_id(pack_id_str)
        if not all_pack_questions: return []
        effective_count = min(target_count, len(all_pack_questions))
        pack_question_ids = [q.id for q in all_pack_questions]
        seen_question_ids = await self.user_question_history_repo.get_seen_question_ids_for_users(
            user_ids=participant_user_ids, question_ids=pack_question_ids
        )
        unseen_questions: List[Question] = []
        seen_questions: List[Question] = []
        for q in all_pack_questions: (seen_questions if q.id in seen_question_ids else unseen_questions).append(q)
        selected_questions_for_game: List[Question] = []
        random.shuffle(unseen_questions); random.shuffle(seen_questions)
        take_from_unseen = min(effective_count, len(unseen_questions))
        selected_questions_for_game.extend(unseen_questions[:take_from_unseen])
        num_needed = effective_count - take_from_unseen
        if num_needed > 0:
            take_from_seen = min(num_needed, len(seen_questions))
            selected_questions_for_game.extend(seen_questions[:take_from_seen])
        random.shuffle(selected_questions_for_game)
        return selected_questions_for_game

    # get_questions_for_play remains unchanged
    async def get_questions_for_play(self, game_session_id: str) -> List[GamePlayQuestionResponse]:
        game_session_id = ensure_uuid(game_session_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game session {game_session_id} not found.")
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)
        if not game_questions: raise ValueError(f"No questions found linked to game session {game_session_id}.")
        fetch_tasks = [
            asyncio.gather( self.question_repo.get_by_id(gq.question_id), self.incorrect_answers_repo.get_by_question_id(gq.question_id), return_exceptions=True )
            for gq in game_questions
        ]
        fetched_data = await asyncio.gather(*fetch_tasks)
        play_questions: List[GamePlayQuestionResponse] = []
        for i, (gq, data) in enumerate(zip(game_questions, fetched_data)):
            original_question, incorrect_answers_record = data
            if isinstance(original_question, Exception) or not original_question: logger.error(f"Failed to fetch original question {gq.question_id}: {original_question}"); continue
            incorrect_options = []
            if isinstance(incorrect_answers_record, Exception): logger.error(f"Failed to fetch incorrect answers for {gq.question_id}: {incorrect_answers_record}")
            else: incorrect_options = incorrect_answers_record.incorrect_answers if incorrect_answers_record else []
            correct_answer_text = original_question.answer; all_options_texts = [correct_answer_text] + incorrect_options; random.shuffle(all_options_texts)
            correct_answer_id = None
            for index, option_text in enumerate(all_options_texts):
                 answer_id = f"{gq.question_id}-{index}"
                 if option_text == correct_answer_text: correct_answer_id = answer_id; break
            if correct_answer_id is None: logger.error(f"Could not determine correct_answer_id for question {gq.question_id}"); continue
            shuffled_option_texts_only = all_options_texts
            play_question = GamePlayQuestionResponse( index=gq.question_index, question_id=gq.question_id, question_text=original_question.question, options=shuffled_option_texts_only, correct_answer_id=correct_answer_id, time_limit=game_session.time_limit_seconds )
            play_questions.append(play_question)
        play_questions.sort(key=lambda q: q.index)
        return play_questions

    # _advance_to_next_question remains unchanged
    # NOTE: Broadcast logic is moved to `end_current_question` which calls this.
    async def _advance_to_next_question(
        self,
        game_session_id: str,
        next_index: Optional[int] = None
    ) -> Optional[GameQuestion]:
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
            return None # Indicates game end
        # Update the game session's current index
        updated_session = await self.game_session_repo.update(id=game_session_id, obj_in=GameSessionUpdate(current_question_index=next_index) )# type: ignore[call-arg]
        if not updated_session: logger.error(f"Failed to update current_question_index for game {game_session_id}"); return None
        # Get the corresponding GameQuestion record
        next_game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id=game_session_id, question_index=next_index)
        if next_game_question:
            # Mark the question as started (sets start_time) - Note: Timer start should be triggered by client receiving the WS message
            started_question = await self.game_question_repo.start_question(next_game_question.id)
            if started_question: logger.info(f"Game {game_session_id} advanced to question {next_index}"); return started_question
            else: logger.error(f"Failed to mark game question {next_game_question.id} as started for game {game_session_id}"); return None
        else: logger.error(f"Game {game_session_id}: Failed to find game question at index {next_index}"); return None

    # submit_answer remains unchanged in core logic, but could broadcast scores
    # (For simplicity, we'll only broadcast on `end_current_question` for now)
    async def submit_answer(
        self,
        game_session_id: str,
        participant_id: str,
        question_index: int,
        answer: str
    ) -> Dict[str, Any]:
        game_session_id = ensure_uuid(game_session_id); participant_id = ensure_uuid(participant_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id);
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game not active")
        participant = await self.game_participant_repo.get_by_id(participant_id);
        if not participant or participant.game_session_id != game_session_id: raise ValueError(f"Participant not found in game")
        game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id, question_index);
        if not game_question: raise ValueError(f"Question index {question_index} not found")
        if game_session.current_question_index != question_index: raise ValueError(f"Not the current question")
        if not game_question.start_time: raise ValueError(f"Question not started")
        if game_question.end_time: raise ValueError(f"Question ended")
        if participant_id in game_question.participant_answers: raise ValueError("Answer already submitted")
        await self.game_question_repo.record_participant_answer(game_question.id, participant_id, answer)
        original_question = await self.question_repo.get_by_id(game_question.question_id)
        if not original_question: logger.error(f"Original question {game_question.question_id} not found"); return {"success": False, "error": "Original question data missing"}
        is_correct = answer.lower().strip() == original_question.answer.lower().strip(); score = 0
        if is_correct:
            max_score = 1000; now = datetime.now(timezone.utc); start_time = game_question.start_time
            if start_time:
                 if start_time.tzinfo is None: start_time = start_time.replace(tzinfo=timezone.utc)
                 try:
                     seconds_taken = (now - start_time).total_seconds(); time_limit = max(game_session.time_limit_seconds, 1)
                     time_factor = max(0, 1 - (seconds_taken / time_limit)) if time_limit > 0 else 1
                     score = max(int(max_score * time_factor), 100)
                 except Exception as e: logger.error(f"Time calculation error: {e}"); score = 100
            else: logger.warning("Start time missing"); score = 100
        await self.game_question_repo.record_participant_score(game_question.id, participant_id, score)
        new_total_score = participant.score + score; updated_participant = await self.game_participant_repo.update_score(participant_id, new_total_score)
        final_total_score = updated_participant.score if updated_participant else new_total_score
        try:
            history_data = UserQuestionHistoryCreate(user_id=participant.user_id, question_id=game_question.question_id, correct=is_correct)
            await self.user_question_history_repo.create(obj_in=history_data)
        except Exception as hist_error: logger.error(f"Failed to record question history: {hist_error}", exc_info=True)
        return {"success": True, "is_correct": is_correct, "correct_answer": original_question.answer, "score": score, "total_score": final_total_score}

    # --- MODIFIED end_current_question ---
    async def end_current_question(
        self,
        game_session_id: str,
        host_user_id: str
    ) -> Dict[str, Any]:
        """Ends the current question, calculates results/scores for it, advances the game, and broadcasts the next step."""
        game_session_id = ensure_uuid(game_session_id); host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only host can end question/advance game")
        if game_session.status != GameStatus.ACTIVE: raise ValueError(f"Game not active")

        current_index = game_session.current_question_index
        current_game_question = await self.game_question_repo.get_by_game_session_and_index(game_session_id, current_index)

        # End the current question in DB if not already ended
        if current_game_question and current_game_question.start_time and not current_game_question.end_time:
             ended_question = await self.game_question_repo.end_question(current_game_question.id)
             if ended_question: current_game_question = ended_question # Use updated record
             else: logger.warning(f"Failed to mark question {current_index} as ended.")
        elif not current_game_question: logger.warning(f"Current game question (index {current_index}) not found when trying to end it.")

        # --- Broadcast Question Results/Scores ---
        # (Optional - could make WS chatty, maybe only send on game end?)
        # participant_scores = current_game_question.participant_scores if current_game_question else {}
        # score_update_message = {
        #     "type": "question_results",
        #     "payload": {"question_index": current_index, "scores": participant_scores}
        # }
        # await self.connection_manager.broadcast(score_update_message, game_session_id)
        # --- End Broadcast ---

        # Advance to the next question or get game end signal
        next_game_question = await self._advance_to_next_question(game_session_id)

        if next_game_question:
            # Fetch formatted next question details
            play_questions = await self.get_questions_for_play(game_session_id)
            next_question_payload = next((q for q in play_questions if q.index == next_game_question.question_index), None)

            if next_question_payload:
                # --- Broadcast Next Question Event ---
                next_q_message = {"type": "next_question", "payload": next_question_payload}
                await self.connection_manager.broadcast(next_q_message, game_session_id)
                logger.info(f"Broadcasted next_question event (index {next_game_question.question_index}) for game {game_session_id}")
                # --- End Broadcast ---
                return {"game_complete": False, "next_question_index": next_game_question.question_index} # Return minimal REST response
            else:
                 logger.error(f"Failed to format next question payload for index {next_game_question.question_index} in game {game_session_id}")
                 # Consider broadcasting an error or ending game? For now, return error state.
                 return {"game_complete": False, "error": "Failed to load next question data"}
        else:
            # Game has ended (or failed to advance)
            final_game_session = await self.game_session_repo.get_by_id(game_session_id) # Re-fetch to confirm status
            if final_game_session and final_game_session.status == GameStatus.COMPLETED:
                 final_results = await self.get_game_results(game_session_id)
                 # --- Broadcast Game End Event ---
                 end_message = {"type": "game_over", "payload": final_results}
                 await self.connection_manager.broadcast(end_message, game_session_id)
                 logger.info(f"Broadcasted game_over event for game {game_session_id}")
                 # --- End Broadcast ---
                 return {"game_complete": True} # Minimal REST response
            else:
                 logger.warning(f"Game {game_session_id} advance returned None, but status is {final_game_session.status if final_game_session else 'Not Found'}. Ending game.")
                 # Force status update just in case
                 await self.game_session_repo.update_game_status(game_id=game_session_id, status=GameStatus.COMPLETED)
                 final_results = await self.get_game_results(game_session_id) # Get results again
                 end_message = {"type": "game_over", "payload": final_results}
                 await self.connection_manager.broadcast(end_message, game_session_id)
                 return {"game_complete": True}
    # --- END MODIFIED end_current_question ---

    # get_game_participants remains unchanged
    async def get_game_participants(self, game_session_id: str) -> List[Dict[str, Any]]:
        game_session_id_str = ensure_uuid(game_session_id)
        participants: List[GameParticipant] = await self.game_participant_repo.get_by_game_session_id(game_session_id_str)
        return [{"id": p.id, "user_id": p.user_id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]

    # get_game_results remains unchanged
    async def get_game_results(self, game_session_id: str) -> Dict[str, Any]:
        game_session_id = ensure_uuid(game_session_id); game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        # Allow fetching results even if not technically completed (e.g., if cancelled but want final scores)
        # if game_session.status != GameStatus.COMPLETED: logger.warning(f"Requesting results for non-completed game {game_session_id}")
        participants = await self.game_participant_repo.get_by_game_session_id(game_session_id); participants.sort(key=lambda p: p.score, reverse=True)
        game_questions = await self.game_question_repo.get_by_game_session_id(game_session_id)
        question_results = []
        for gq in game_questions:
             original_question = await self.question_repo.get_by_id(gq.question_id)
             if original_question:
                 correct_count = sum(1 for score in gq.participant_scores.values() if score > 0); total_answered = len(gq.participant_answers)
                 correct_percentage = (correct_count / total_answered * 100) if total_answered > 0 else 0
                 question_results.append({"index": gq.question_index, "question_text": original_question.question, "correct_answer": original_question.answer, "correct_count": correct_count, "total_answered": total_answered, "correct_percentage": correct_percentage})
        participant_results = [{"id": p.id, "user_id": p.user_id, "display_name": p.display_name, "score": p.score, "is_host": p.is_host} for p in participants]
        completion_time = game_session.updated_at if game_session.status in [GameStatus.COMPLETED, GameStatus.CANCELLED] else datetime.now(timezone.utc)
        return {"game_id": game_session_id, "game_code": game_session.code, "status": game_session.status.value, "participants": participant_results, "questions": question_results, "total_questions": len(game_questions), "completed_at": completion_time.isoformat()}

    # --- MODIFIED cancel_game ---
    async def cancel_game(self, game_session_id: str, host_user_id: str) -> GameSession:
        game_session_id = ensure_uuid(game_session_id); host_user_id = ensure_uuid(host_user_id)
        game_session = await self.game_session_repo.get_by_id(game_session_id)
        if not game_session: raise ValueError(f"Game {game_session_id} not found")
        if game_session.host_user_id != host_user_id: raise ValueError("Only host can cancel")
        if game_session.status not in [GameStatus.PENDING, GameStatus.ACTIVE]: raise ValueError(f"Game cannot be cancelled (status: {game_session.status})")

        updated_game = await self.game_session_repo.update_game_status(game_id=game_session_id, status=GameStatus.CANCELLED)
        if not updated_game: raise ValueError(f"Failed to cancel game {game_session_id}")

        # --- Broadcast Cancel Event ---
        cancel_message = {"type": "game_cancelled", "payload": {"game_id": game_session_id}}
        await self.connection_manager.broadcast(cancel_message, game_session_id)
        logger.info(f"Broadcasted game_cancelled event for game {game_session_id}")
        # --- End Broadcast ---

        logger.info(f"Game {game_session_id} cancelled by host {host_user_id}")
        return updated_game
    # --- END MODIFIED cancel_game ---

    # --- NEW: handle_disconnect ---
    async def handle_disconnect(self, game_id: str, user_id: str):
        """Handles logic when a user disconnects (called by WS endpoint)."""
        logger.info(f"Handling disconnect for user {user_id} in game {game_id}")
        # Find the participant record
        participant = await self.game_participant_repo.get_by_user_and_game(user_id, game_id)
        if participant:
            # Broadcast user_left message
            message = {"type": "participant_left", "payload": {"user_id": user_id, "participant_id": participant.id, "display_name": participant.display_name}}
            await self.connection_manager.broadcast(message, game_id)
            logger.debug(f"Broadcasted participant_left for user {user_id} in game {game_id}")

            # Optional: Add logic if host disconnects (e.g., cancel game or promote new host)
            # if participant.is_host:
            #    logger.warning(f"Host {user_id} disconnected from game {game_id}. Implement host disconnect logic.")
            #    # await self.cancel_game(game_id, user_id) # Example: cancel if host leaves

        else:
            logger.warning(f"Participant record not found for disconnected user {user_id} in game {game_id}")
    # --- END NEW: handle_disconnect ---

    # get_user_games remains unchanged (it's a REST utility, not real-time)
    async def get_user_games(self, user_id: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        user_id = ensure_uuid(user_id); participations = await self.game_participant_repo.get_user_active_games(user_id)
        results = []; processed_game_ids = set()
        for participation in participations:
             game_session_id = participation.game_session_id
             if game_session_id in processed_game_ids: continue
             game_session = await self.game_session_repo.get_by_id(game_session_id)
             if not game_session: logger.warning(f"Game session {game_session_id} not found for participation {participation.id}"); continue
             if not include_completed and game_session.status in [GameStatus.COMPLETED, GameStatus.CANCELLED]: continue
             participants = await self.game_participant_repo.get_by_game_session_id(game_session.id)
             game_info = {"id": game_session.id, "code": game_session.code, "status": game_session.status.value, "participant_count": len(participants), "max_participants": game_session.max_participants, "current_question": game_session.current_question_index, "total_questions": game_session.question_count, "is_host": participation.is_host, "created_at": game_session.created_at.isoformat(), "updated_at": game_session.updated_at.isoformat()}
             results.append(game_info); processed_game_ids.add(game_session_id)
        return results