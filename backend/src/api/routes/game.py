# backend/src/api/routes/game.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Dict, List, Any, Optional
import logging
import random # Import random
import asyncio # Ensure asyncio is imported

from ..dependencies import get_game_service, get_pack_service
from ..schemas.game import (
    GameSessionCreateRequest, GameSessionJoinRequest, GameSessionSubmitAnswerRequest,
    GameSessionResponse, GameSessionListResponse, QuestionResultResponse, GameResultsResponse,
    GameStartResponse, # <<< Import the new schema
    # --- ADDED IMPORT ---
    GamePlayQuestionListResponse
)
from ...services.game_service import GameService
from ...services.pack_service import PackService
from ...utils import ensure_uuid
from ...models.game_session import GameStatus # Import if needed for direct status comparison

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# --- CREATE GAME ---
@router.post("/create", response_model=GameSessionResponse)
async def create_game(
    game_data: GameSessionCreateRequest = Body(...),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """Create a new multiplayer game session."""
    try:
        user_id = ensure_uuid(user_id)
        pack = await pack_service.pack_repository.get_by_id(game_data.pack_id)
        if not pack:
            raise HTTPException(status_code=404, detail=f"Pack with ID {game_data.pack_id} not found")
        game_session = await game_service.create_game_session(
            host_user_id=user_id, pack_id=game_data.pack_id,
            max_participants=game_data.max_participants,
            question_count=game_data.question_count,
            time_limit_seconds=game_data.time_limit_seconds
        )
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)
        return GameSessionResponse(
            id=game_session.id, code=game_session.code, status=game_session.status,
            pack_id=game_session.pack_id, max_participants=game_session.max_participants,
            question_count=game_session.question_count, time_limit_seconds=game_session.time_limit_seconds,
            current_question_index=game_session.current_question_index,
            participant_count=len(participants), is_host=True, created_at=game_session.created_at
        )
    except ValueError as e:
        logger.error(f"Error creating game: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating game: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")

# --- JOIN GAME ---
@router.post("/join", response_model=GameSessionResponse)
async def join_game(
    join_data: GameSessionJoinRequest = Body(...),
    user_id: str = Query(..., description="ID of the user joining"),
    game_service: GameService = Depends(get_game_service)
):
    """Join an existing game session."""
    try:
        user_id = ensure_uuid(user_id)
        game_session, participant = await game_service.join_game(
            game_code=join_data.game_code, user_id=user_id, display_name=join_data.display_name
        )
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)
        return GameSessionResponse(
             id=game_session.id, code=game_session.code, status=game_session.status,
             pack_id=game_session.pack_id, max_participants=game_session.max_participants,
             question_count=game_session.question_count, time_limit_seconds=game_session.time_limit_seconds,
             current_question_index=game_session.current_question_index,
             participant_count=len(participants), is_host=participant.is_host, created_at=game_session.created_at
         )
    except ValueError as e:
        logger.warning(f"Error joining game {join_data.game_code}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error joining game {join_data.game_code}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to join game: An internal error occurred.")

# --- LIST GAMES ---
@router.get("/list", response_model=GameSessionListResponse)
async def list_games(
    user_id: str = Query(..., description="ID of the user"),
    include_completed: bool = Query(False, description="Whether to include completed games"),
    game_service: GameService = Depends(get_game_service)
):
    """List all games for a user."""
    try:
        user_id = ensure_uuid(user_id)
        games = await game_service.get_user_games(user_id=user_id, include_completed=include_completed)
        return GameSessionListResponse(total=len(games), games=games)
    except Exception as e:
        logger.error(f"Error listing games for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list games: {str(e)}")

# --- START GAME ---
@router.post("/{game_id}/start", response_model=GameStartResponse)
async def start_game_endpoint(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """Start a game session. Returns the status and first question."""
    try:
        game_id = ensure_uuid(game_id); user_id = ensure_uuid(user_id)
        game_session = await game_service.start_game(game_session_id=game_id, host_user_id=user_id)
        game_question = await game_service.game_question_repo.get_by_game_session_and_index(game_id, 0)
        if not game_question: raise HTTPException(status_code=500, detail="Failed to retrieve first question")
        original_question = await game_service.question_repo.get_by_id(game_question.question_id)
        if not original_question: raise HTTPException(status_code=500, detail="Failed to retrieve original question data")
        incorrect_answers = await game_service.incorrect_answers_repo.get_by_question_id(game_question.question_id)
        incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []
        all_options = [original_question.answer] + incorrect_options; random.shuffle(all_options)
        response_data = {"status": game_session.status, "current_question": {"index": 0, "question_text": original_question.question, "options": all_options, "time_limit": game_session.time_limit_seconds}}
        return response_data
    except ValueError as e:
        logger.warning(f"Validation error starting game {game_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start game: An internal error occurred.")

# --- GET PLAY QUESTIONS (NEW ENDPOINT) ---
@router.get("/{game_id}/play-questions", response_model=GamePlayQuestionListResponse)
async def get_gameplay_questions(
    game_id: str = Path(..., description="ID of the game session"),
    game_service: GameService = Depends(get_game_service)
):
    """Get the list of questions (with shuffled options) for an active game."""
    try:
        game_id_str = ensure_uuid(game_id)
        play_questions = await game_service.get_questions_for_play(game_id_str)
        return GamePlayQuestionListResponse(
            game_id=game_id_str,
            questions=play_questions,
            total_questions=len(play_questions)
        )
    except ValueError as e:
        logger.warning(f"Error getting gameplay questions for game {game_id}: {str(e)}")
        # Distinguish between not found and other value errors
        status_code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting gameplay questions for game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve game questions.")
# --- END GET PLAY QUESTIONS ---

# --- SUBMIT ANSWER ---
@router.post("/{game_id}/submit", response_model=QuestionResultResponse)
async def submit_answer(
    game_id: str = Path(..., description="ID of the game session"),
    participant_id: str = Query(..., description="ID of the participant"),
    answer_data: GameSessionSubmitAnswerRequest = Body(...),
    game_service: GameService = Depends(get_game_service)
):
    """Submit an answer for a question."""
    try:
        game_id = ensure_uuid(game_id); participant_id = ensure_uuid(participant_id)
        result = await game_service.submit_answer(
            game_session_id=game_id, participant_id=participant_id,
            question_index=answer_data.question_index, answer=answer_data.answer
        )
        if not result.get("success", True): raise ValueError(result.get("error", "Failed to submit answer."))
        return QuestionResultResponse(
            is_correct=result.get("is_correct", False), correct_answer=result.get("correct_answer", ""),
            score=result.get("score", 0), total_score=result.get("total_score", 0)
        )
    except ValueError as e:
        logger.warning(f"Error submitting answer for game {game_id}, participant {participant_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error submitting answer for game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

# --- NEXT QUESTION ---
@router.post("/{game_id}/next", response_model=Dict[str, Any])
async def next_question(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """Advance to the next question or end the game."""
    try:
        game_id = ensure_uuid(game_id); user_id = ensure_uuid(user_id)
        result = await game_service.end_current_question(game_session_id=game_id, host_user_id=user_id)
        return result
    except ValueError as e:
        logger.warning(f"Error advancing question for game {game_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error advancing question for game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to advance question: {str(e)}")

# --- CANCEL GAME ---
@router.post("/{game_id}/cancel")
async def cancel_game(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """Cancel an active or pending game."""
    try:
        game_id = ensure_uuid(game_id); user_id = ensure_uuid(user_id)
        game_session = await game_service.cancel_game(game_session_id=game_id, host_user_id=user_id)
        return {"id": game_session.id, "status": game_session.status.value, "message": "Game successfully cancelled"}
    except ValueError as e:
        logger.warning(f"Error cancelling game {game_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error cancelling game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel game: {str(e)}")

# --- GET RESULTS ---
@router.get("/{game_id}/results", response_model=GameResultsResponse)
async def get_results(
    game_id: str = Path(..., description="ID of the game session"),
    game_service: GameService = Depends(get_game_service)
):
    """Get results for a completed game."""
    try:
        game_id = ensure_uuid(game_id)
        results = await game_service.get_game_results(game_id)
        return results
    except ValueError as e:
        logger.warning(f"Error getting results for game {game_id}: {str(e)}")
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting results for game {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get game results: {str(e)}")

# --- GET PARTICIPANTS ---
@router.get("/{game_id}/participants")
async def get_participants_endpoint(
    game_id: str = Path(..., description="ID of the game session"),
    game_service: GameService = Depends(get_game_service)
):
    """Get participants for a game session."""
    try:
        game_id_str = ensure_uuid(game_id)
        participants_data = await game_service.get_game_participants(game_id_str)
        return {"total": len(participants_data), "participants": participants_data}
    except Exception as e:
        logger.error(f"Error getting game participants for {game_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get game participants: {str(e)}")