# backend/src/api/routes/game.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Dict, List, Any, Optional
import logging

from ..dependencies import get_game_service, get_pack_service
from ..schemas.game import (
    GameSessionCreateRequest, GameSessionJoinRequest, GameSessionSubmitAnswerRequest,
    GameSessionResponse, GameSessionListResponse, QuestionResultResponse, GameResultsResponse
)
from ...services.game_service import GameService
from ...services.pack_service import PackService
from ...utils import ensure_uuid

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
    
    Args:
        game_data: Game session creation parameters
        user_id: ID of the host user
        game_service: Game service dependency
        
    Returns:
        Created game session
    """
    try:
        # Ensure user_id is a valid UUID string
        user_id = ensure_uuid(user_id)
        
        # Verify the pack exists
        pack = await pack_service.pack_repository.get_by_id(game_data.pack_id)
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {game_data.pack_id} not found"
            )
        
        # Create the game session
        game_session = await game_service.create_game_session(
            host_user_id=user_id,
            pack_id=game_data.pack_id,
            max_participants=game_data.max_participants,
            question_count=game_data.question_count,
            time_limit_seconds=game_data.time_limit_seconds
        )
        
        # Get participants to include the count
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)
        
        return {
            **game_session.dict(),
            "participant_count": len(participants),
            "is_host": True  # Creator is always the host
        }
    
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
    
    Args:
        join_data: Game join parameters
        user_id: ID of the user joining
        game_service: Game service dependency
        
    Returns:
        Game session joined
    """
    try:
        # Ensure user_id is a valid UUID string
        user_id = ensure_uuid(user_id)
        
        # Join the game
        game_session, participant = await game_service.join_game(
            game_code=join_data.game_code,
            user_id=user_id,
            display_name=join_data.display_name
        )
        
        # Get all participants to include the count
        participants = await game_service.game_participant_repo.get_by_game_session_id(game_session.id)
        
        return {
            **game_session.dict(),
            "participant_count": len(participants),
            "is_host": participant.is_host
        }
    
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
    
    Args:
        user_id: ID of the user
        include_completed: Whether to include completed games
        game_service: Game service dependency
        
    Returns:
        List of game sessions
    """
    try:
        # Ensure user_id is a valid UUID string
        user_id = ensure_uuid(user_id)
        
        # Get user's games
        games = await game_service.get_user_games(
            user_id=user_id,
            include_completed=include_completed
        )
        
        return {
            "total": len(games),
            "games": games
        }
    
    except Exception as e:
        logger.error(f"Error listing games: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list games: {str(e)}"
        )

@router.post("/{game_id}/start")
async def start_game(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Start a game session.
    
    Args:
        game_id: ID of the game session
        user_id: ID of the host user
        game_service: Game service dependency
        
    Returns:
        Game session status and first question
    """
    try:
        # Ensure IDs are valid UUID strings
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)
        
        # Start the game
        game_session = await game_service.start_game(
            game_session_id=game_id,
            host_user_id=user_id
        )
        
        # Get the first question
        game_question = await game_service.game_question_repo.get_by_game_session_and_index(
            game_session_id=game_id,
            question_index=0
        )
        
        if not game_question:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve first question"
            )
            
        # Get the original question
        original_question = await game_service.question_repo.get_by_id(game_question.question_id)
        if not original_question:
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve question data"
            )
            
        # Get incorrect answers
        incorrect_answers = await game_service.incorrect_answers_repo.get_by_question_id(game_question.question_id)
        incorrect_options = incorrect_answers.incorrect_answers if incorrect_answers else []
        
        # Combine and shuffle options
        import random
        all_options = [original_question.answer] + incorrect_options
        random.shuffle(all_options)
        
        return {
            "status": game_session.status,
            "current_question": {
                "index": 0,
                "question_text": original_question.question,
                "options": all_options,
                "time_limit": game_session.time_limit_seconds
            }
        }
    
    except ValueError as e:
        logger.error(f"Error starting game: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error starting game: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start game: {str(e)}"
        )

@router.post("/{game_id}/submit", response_model=QuestionResultResponse)
async def submit_answer(
    game_id: str = Path(..., description="ID of the game session"),
    participant_id: str = Query(..., description="ID of the participant"),
    answer_data: GameSessionSubmitAnswerRequest = Body(...),
    game_service: GameService = Depends(get_game_service)
):
    """
    Submit an answer for a question.
    
    Args:
        game_id: ID of the game session
        participant_id: ID of the participant
        answer_data: Answer submission data
        game_service: Game service dependency
        
    Returns:
        Result of the answer submission
    """
    try:
        # Ensure IDs are valid UUID strings
        game_id = ensure_uuid(game_id)
        participant_id = ensure_uuid(participant_id)
        
        # Submit the answer
        result = await game_service.submit_answer(
            game_session_id=game_id,
            participant_id=participant_id,
            question_index=answer_data.question_index,
            answer=answer_data.answer
        )
        
        return result
    
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

@router.post("/{game_id}/next")
async def next_question(
    game_id: str = Path(..., description="ID of the game session"),
    user_id: str = Query(..., description="ID of the host user"),
    game_service: GameService = Depends(get_game_service)
):
    """
    Advance to the next question or end the game.
    
    Args:
        game_id: ID of the game session
        user_id: ID of the host user
        game_service: Game service dependency
        
    Returns:
        Next question or game results
    """
    try:
        # Ensure IDs are valid UUID strings
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)
        
        # End current question and advance
        result = await game_service.end_current_question(
            game_session_id=game_id,
            host_user_id=user_id
        )
        
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
    
    Args:
        game_id: ID of the game session
        user_id: ID of the host user
        game_service: Game service dependency
        
    Returns:
        Cancelled game status
    """
    try:
        # Ensure IDs are valid UUID strings
        game_id = ensure_uuid(game_id)
        user_id = ensure_uuid(user_id)
        
        # Cancel the game
        game_session = await game_service.cancel_game(
            game_session_id=game_id,
            host_user_id=user_id
        )
        
        return {
            "id": game_session.id,
            "status": game_session.status,
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
    
    Args:
        game_id: ID of the game session
        game_service: Game service dependency
        
    Returns:
        Game results
    """
    try:
        # Ensure game_id is a valid UUID string
        game_id = ensure_uuid(game_id)
        
        # Get game results
        results = await game_service.get_game_results(game_id)
        
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
    
    Args:
        game_id: ID of the game session
        game_service: Game service dependency
        
    Returns:
        List of participants
    """
    try:
        # Ensure game_id is a valid UUID string
        game_id = ensure_uuid(game_id)
        
        # Get participants
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