# backend/src/api/routes/game.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Dict, List, Any, Optional
import logging
import random # Import random

from ..dependencies import get_game_service, get_pack_service
from ..schemas.game import (
    GameSessionCreateRequest, GameSessionJoinRequest, GameSessionSubmitAnswerRequest,
    GameSessionResponse, GameSessionListResponse, QuestionResultResponse, GameResultsResponse,
    GameStartResponse # <<< Import the new schema
)
from ...services.game_service import GameService
from ...services.pack_service import PackService
from ...utils import ensure_uuid
from ...models.game_session import GameStatus # Import if needed for direct status comparison

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=GameSessionResponse)
async def create_game(
    game_data: GameSessionCreateRequest = Body(...),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Create a new multiplayer game session.
    """
    try:
        user_id = ensure_uuid(user_id)
        pack = await pack_service.pack_repository.get_by_id(game_data.pack_id)
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {game_data.pack_id} not found"
            )

        game_session = await game_service.create_game_session(
            host_user_id=user_id,
            pack_id=game_data.pack_id,
            max_participants=game_data.max_participants,
            question_count=game_data.question_count,
            time_limit_seconds=game_data.time_limit_seconds
        )

        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)

        # Ensure the response matches the schema
        return GameSessionResponse(
            id=game_session.id,
            code=game_session.code,
            status=game_session.status,
            pack_id=game_session.pack_id,
            max_participants=game_session.max_participants,
            question_count=game_session.question_count,
            time_limit_seconds=game_session.time_limit_seconds,
            current_question_index=game_session.current_question_index,
            participant_count=len(participants),
            is_host=True, # Creator is always the host initially
            created_at=game_session.created_at
        )

    except ValueError as e:
        logger.error(f"Error creating game: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating game: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create game: {str(e)}"
        )

@router.post("/join", response_model=GameSessionResponse)
async def join_game(
    join_data: GameSessionJoinRequest = Body(...),
    user_id: str = Query(..., description="ID of the user joining"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Join an existing game session.
    """
    try:
        user_id = ensure_uuid(user_id)
        game_session, participant = await game_service.join_game(
            game_code=join_data.game_code,
            user_id=user_id,
            display_name=join_data.display_name
        )
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)

        # Ensure the response matches the schema
        return GameSessionResponse(
             id=game_session.id,
             code=game_session.code,
             status=game_session.status,
             pack_id=game_session.pack_id,
             max_participants=game_session.max_participants,
             question_count=game_session.question_count,
             time_limit_seconds=game_session.time_limit_seconds,
             current_question_index=game_session.current_question_index,
             participant_count=len(participants),
             is_host=participant.is_host, # Use the participant's host status
             created_at=game_session.created_at
         )

    except ValueError as e:
        logger.error(f"Error joining game: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error joining game: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to join game: {str(e)}"
        )

@router.get("/list", response_model=GameSessionListResponse)
async def list_games(
    user_id: str = Query(..., description="ID of the user"),
    include_completed: bool = Query(False, description="Whether to include completed games"),
    game_service: GameService = Depends(get_game_service)
):
    """
    List all games for a user.
    """
    try:
        user_id = ensure_uuid(user_id)
        games = await game_service.get_user_games(
            user_id=user_id,
            include_completed=include_completed
        )

        return GameSessionListResponse(
            total=len(games),
            games=games # Assumes service returns list of dicts compatible with Any
        )

    except Exception as e:
        logger.error(f"Error listing games: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list games: {str(e)}"
        )

# --- FIX: Added response_model ---
@router.post("/{game_id}/start", response_model=GameStartResponse)
async def start_game(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Start a game session. Returns the status and first question.
    """
    try:
        # Ensure IDs are valid UUID strings
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)

        # Start the game (returns updated GameSession)
        game_session = await game_service.start_game(
            game_session_id=game_id,
            host_user_id=user_id
        )

        # Get the first question (index 0 is set by start_game)
        # Service layer ensures game questions are created before returning
        game_question = await game_service.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_id,
            question_index=0
        )

        if not game_question:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve first question after starting game"
            )

        # Get the original question
        original_question = await game_service.question_repo.get_by_id(game_question.question_id)
        if not original_question:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve original question data"
            )

        # Get incorrect answers
        incorrect_answers = await game_service.incorrect_answers_repo.get_by_question_id(game_question.question_id)
        incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []

        # Combine and shuffle options
        all_options = [original_question.answer] + incorrect_options
        random.shuffle(all_options)

        # --- FIX: Construct the response dictionary matching GameStartResponse ---
        response_data = {
            "status": game_session.status,
            "current_question": {
                "index": 0,
                "question_text": original_question.question,
                "options": all_options,
                "time_limit": game_session.time_limit_seconds
            }
        }
        # FastAPI will now validate this dict against GameStartResponse and serialize correctly
        return response_data

    except ValueError as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error starting game: {str(e)}", exc_info=True) # Log traceback
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start game: An internal error occurred." # Avoid exposing internal error details
        )
# --- END FIX ---


@router.post("/{game_id}/submit", response_model=QuestionResultResponse)
async def submit_answer(
    game_id: str = Path(..., description="ID of the game session"),
    participant_id: str = Query(..., description="ID of the participant"),
    answer_data: GameSessionSubmitAnswerRequest = Body(...),
    game_service: GameService = Depends(get_game_service)
):
    """
    Submit an answer for a question.
    """
    try:
        game_id = ensure_uuid(game_id)
        participant_id = ensure_uuid(participant_id)

        result = await game_service.submit_answer(
            game_session_id=game_id,
            participant_id=participant_id,
            question_index=answer_data.question_index,
            answer=answer_data.answer
        )

        # Ensure response matches schema
        return QuestionResultResponse(
            is_correct=result.get("is_correct", False),
            correct_answer=result.get("correct_answer", ""),
            score=result.get("score", 0),
            total_score=result.get("total_score", 0)
        )

    except ValueError as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error submitting answer: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit answer: {str(e)}"
        )

# --- FIX: Define response model for next_question ---
# It can return either the next question details or the final results
# We can use Union or create a more complex response model,
# but for simplicity, let's return Dict[str, Any] and let the client handle it
@router.post("/{game_id}/next", response_model=Dict[str, Any])
async def next_question(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Advance to the next question or end the game.
    """
    try:
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)

        result = await game_service.end_current_question(
            game_session_id=game_id,
            host_user_id=user_id
        )

        # The result structure depends on whether the game ended or not
        # The service layer prepares this dictionary. Pydantic V2 handles datetime/enum.
        return result

    except ValueError as e:
        logger.error(f"Error advancing question: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error advancing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to advance question: {str(e)}"
        )

@router.post("/{game_id}/cancel")
async def cancel_game(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Cancel an active or pending game.
    """
    try:
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)

        game_session = await game_service.cancel_game(
            game_session_id=game_id,
            host_user_id=user_id
        )

        return {
            "id": game_session.id,
            "status": game_session.status.value, # Return enum value
            "message": "Game successfully cancelled"
        }

    except ValueError as e:
        logger.error(f"Error cancelling game: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error cancelling game: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel game: {str(e)}"
        )

@router.get("/{game_id}/results", response_model=GameResultsResponse)
async def get_results(
    game_id: str = Path(..., description="ID of the game session"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Get results for a completed game.
    """
    try:
        game_id = ensure_uuid(game_id)
        results = await game_service.get_game_results(game_id)

        # The service should return data compatible with GameResultsResponse
        # Pydantic will handle the datetime/enum serialization
        return results

    except ValueError as e:
        logger.error(f"Error getting game results: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting game results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game results: {str(e)}"
        )

@router.get("/{game_id}/participants")
async def get_participants(
    game_id: str = Path(..., description="ID of the game session"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Get participants for a game session.
    """
    try:
        game_id = ensure_uuid(game_id)
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_id)

        return {
            "total": len(participants),
            "participants": [
                {
                    "id": p.id,
                    "display_name": p.display_name,
                    "score": p.score,
                    "is_host": p.is_host
                }
                for p in participants
            ]
        }

    except Exception as e:
        logger.error(f"Error getting game participants: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get game participants: {str(e)}"
        )