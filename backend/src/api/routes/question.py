# backend/src/api/routes/question.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Optional, List
import logging

from ..dependencies import get_question_service, get_seed_question_service, get_difficulty_service
from ..schemas import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse
)
from ...services.question_service import QuestionService
from ...services.seed_question_service import SeedQuestionService
from ...services.difficulty_service import DifficultyService
from ...models.question import DifficultyLevel
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=QuestionsResponse)
async def generate_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    question_request: QuestionGenerateRequest = Body(...),
    question_service: QuestionService = Depends(get_question_service),
    difficulty_service: DifficultyService = Depends(get_difficulty_service),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service)
):
    """
    Generate trivia questions for a pack.
    
    Args:
        pack_id: ID of the pack
        question_request: Request data for question generation
        question_service: Question service dependency
        difficulty_service: Difficulty service dependency
        seed_question_service: Seed question service dependency
        
    Returns:
        Generated questions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Get difficulty descriptions
        difficulty_descriptions = await difficulty_service.get_existing_difficulty_descriptions(pack_id)
        
        # Get seed questions if available
        seed_questions = await seed_question_service.get_seed_questions(pack_id)
        
        # Generate questions
        questions = await question_service.generate_and_store_questions(
            pack_id=pack_id,
            creation_name="Pack Name",  # This should come from the pack service
            pack_topic=question_request.pack_topic,
            difficulty=question_request.difficulty,
            num_questions=question_request.num_questions,
            debug_mode=question_request.debug_mode
        )
        
        return QuestionsResponse(
            total=len(questions),
            questions=questions
        )
    
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )

@router.get("/", response_model=QuestionsResponse)
async def get_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    skip: int = Query(0, ge=0, description="Number of questions to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of questions to return"),
    question_service: QuestionService = Depends(get_question_service)
):
    """
    Get questions for a pack with optional filtering.
    
    Args:
        pack_id: ID of the pack
        topic: Optional filter by topic
        difficulty: Optional filter by difficulty
        skip: Number of questions to skip (pagination)
        limit: Number of questions to return (pagination)
        question_service: Question service dependency
        
    Returns:
        Questions matching the criteria
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Get questions
        if topic:
            questions = await question_service.get_questions_by_topic(pack_id, topic)
        else:
            questions = await question_service.get_questions_by_pack_id(pack_id)
        
        # Filter by difficulty if provided
        if difficulty:
            questions = [q for q in questions if q.difficulty_current == difficulty]
        
        # Apply pagination
        total = len(questions)
        paginated_questions = questions[skip:skip + limit]
        
        return QuestionsResponse(
            total=total,
            questions=paginated_questions
        )
    
    except Exception as e:
        logger.error(f"Error retrieving questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving questions: {str(e)}"
        )

@router.post("/seed", response_model=SeedQuestionsResponse)
async def store_seed_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_request: SeedQuestionRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service)
):
    """
    Store seed questions for a pack.
    
    Args:
        pack_id: ID of the pack
        seed_request: Request data containing seed questions
        seed_question_service: Seed question service dependency
        
    Returns:
        Stored seed questions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Store seed questions
        success = await seed_question_service.store_seed_questions(
            pack_id=pack_id,
            seed_questions=seed_request.seed_questions
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to store seed questions. Pack creation data might not exist."
            )
        
        return SeedQuestionsResponse(
            count=len(seed_request.seed_questions),
            seed_questions=seed_request.seed_questions
        )
    
    except Exception as e:
        logger.error(f"Error storing seed questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error storing seed questions: {str(e)}"
        )

@router.post("/seed/extract", response_model=SeedQuestionsResponse)
async def extract_seed_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    text_request: SeedQuestionTextRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service)
):
    """
    Extract and store seed questions from text.
    
    Args:
        pack_id: ID of the pack
        text_request: Request data containing text to process
        seed_question_service: Seed question service dependency
        
    Returns:
        Extracted and stored seed questions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Extract seed questions from text
        extracted_questions = await seed_question_service.seed_processor.detect_and_process_input(
            text_request.text_content
        )
        
        if not extracted_questions:
            raise HTTPException(
                status_code=400,
                detail="No questions could be extracted from the provided text."
            )
        
        # Store the extracted questions
        success = await seed_question_service.store_seed_questions(
            pack_id=pack_id,
            seed_questions=extracted_questions
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to store extracted questions. Pack creation data might not exist."
            )
        
        return SeedQuestionsResponse(
            count=len(extracted_questions),
            seed_questions=extracted_questions
        )
    
    except Exception as e:
        logger.error(f"Error extracting seed questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting seed questions: {str(e)}"
        )

@router.get("/seed", response_model=SeedQuestionsResponse)
async def get_seed_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service)
):
    """
    Get seed questions for a pack.
    
    Args:
        pack_id: ID of the pack
        seed_question_service: Seed question service dependency
        
    Returns:
        Stored seed questions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    try:
        # Get seed questions
        seed_questions = await seed_question_service.get_seed_questions(pack_id)
        
        return SeedQuestionsResponse(
            count=len(seed_questions),
            seed_questions=seed_questions
        )
    
    except Exception as e:
        logger.error(f"Error retrieving seed questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving seed questions: {str(e)}"
        )