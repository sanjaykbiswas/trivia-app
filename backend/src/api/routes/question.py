# backend/src/api/routes/question.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Optional, List
import logging

from ..dependencies import get_question_service, get_seed_question_service, get_difficulty_service, get_pack_service, get_incorrect_answer_service
from ..schemas import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse,
    CustomInstructionsGenerateRequest, CustomInstructionsInputRequest, CustomInstructionsResponse
)
from ...services.question_service import QuestionService
from ...services.seed_question_service import SeedQuestionService
from ...services.difficulty_service import DifficultyService
from ...services.pack_service import PackService
from ...services.incorrect_answer_service import IncorrectAnswerService
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
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
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
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Get difficulty descriptions
        difficulty_descriptions = await difficulty_service.get_existing_difficulty_descriptions(pack_id)
        
        # Get seed questions if available
        seed_questions = await seed_question_service.get_seed_questions(pack_id)
        
        # Generate questions
        questions = await question_service.generate_and_store_questions(
            pack_id=pack_id,
            creation_name=pack.name,
            pack_topic=question_request.pack_topic,
            difficulty=question_request.difficulty,
            num_questions=question_request.num_questions,
            debug_mode=question_request.debug_mode,
            custom_instructions=question_request.custom_instructions
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
    question_service: QuestionService = Depends(get_question_service),
    pack_service: PackService = Depends(get_pack_service)
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
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
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
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
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
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Check if we have pack creation data already
        pack_creation_data = await seed_question_service.pack_creation_repository.get_by_pack_id(pack_id)
        
        # If not, we need to create it first
        if not pack_creation_data:
            # Create basic pack creation data
            from ...models.pack_creation_data import PackCreationDataCreate
            
            creation_data = PackCreationDataCreate(
                pack_id=pack_id,
                creation_name=pack.name,
                pack_topics=[]  # Start with empty topics list
            )
            
            await seed_question_service.pack_creation_repository.create(obj_in=creation_data)
        
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
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
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
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
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
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
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
        
        # Check if we have pack creation data already
        pack_creation_data = await seed_question_service.pack_creation_repository.get_by_pack_id(pack_id)
        
        # If not, we need to create it first
        if not pack_creation_data:
            # Create basic pack creation data
            from ...models.pack_creation_data import PackCreationDataCreate
            
            creation_data = PackCreationDataCreate(
                pack_id=pack_id,
                creation_name=pack.name,
                pack_topics=[]  # Start with empty topics list
            )
            
            await seed_question_service.pack_creation_repository.create(obj_in=creation_data)
        
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
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error extracting seed questions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting seed questions: {str(e)}"
        )

@router.get("/seed", response_model=SeedQuestionsResponse)
async def get_seed_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
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
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Get seed questions
        seed_questions = await seed_question_service.get_seed_questions(pack_id)
        
        # Even if no seed questions are found, return an empty dictionary
        # rather than raising an error
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

# New custom instructions endpoints
@router.post("/custom-instructions/generate", response_model=CustomInstructionsResponse)
async def generate_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsGenerateRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate custom instructions for question generation.
    
    Args:
        pack_id: ID of the pack
        request: Request data for custom instructions generation
        seed_question_service: Seed question service dependency
        
    Returns:
        Generated custom instructions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Generate custom instructions
        custom_instructions = await seed_question_service.generate_custom_instructions(
            pack_id=pack_id,
            pack_topic=request.pack_topic
        )
        
        if custom_instructions is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate or store custom instructions"
            )
        
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error generating custom instructions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating custom instructions: {str(e)}"
        )

@router.post("/custom-instructions/input", response_model=CustomInstructionsResponse)
async def input_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsInputRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Input custom instructions for question generation.
    
    Args:
        pack_id: ID of the pack
        request: Request data with manually provided custom instructions
        seed_question_service: Seed question service dependency
        
    Returns:
        Processed and stored custom instructions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Process and store manual instructions
        success = await seed_question_service.process_and_store_manual_instructions(
            pack_id=pack_id,
            instructions=request.instructions
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to process or store custom instructions"
            )
        
        # Retrieve the stored instructions
        custom_instructions = await seed_question_service.get_custom_instructions(pack_id)
        
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing custom instructions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing custom instructions: {str(e)}"
        )

@router.get("/custom-instructions", response_model=CustomInstructionsResponse)
async def get_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Get existing custom instructions for a pack.
    
    Args:
        pack_id: ID of the pack
        seed_question_service: Seed question service dependency
        
    Returns:
        Stored custom instructions
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # First verify the pack exists
    try:
        pack_repo = pack_service.pack_repository
        pack = await pack_repo.get_by_id(pack_id)
        
        if not pack:
            raise HTTPException(
                status_code=404,
                detail=f"Pack with ID {pack_id} not found"
            )
    except Exception as e:
        logger.error(f"Error verifying pack existence: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    try:
        # Get custom instructions
        custom_instructions = await seed_question_service.get_custom_instructions(pack_id)
        
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    
    except Exception as e:
        logger.error(f"Error retrieving custom instructions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving custom instructions: {str(e)}"
        )

@router.post("/{question_id}/incorrect-answers")
async def generate_incorrect_answers(
    question_id: str = Path(..., description="ID of the question"),
    num_answers: int = Query(3, ge=1, le=10, description="Number of incorrect answers to generate"),
    debug_mode: bool = Query(False, description="Enable verbose debug output"),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service),
    question_service: QuestionService = Depends(get_question_service)
):
    """
    Generate incorrect answers for a specific question.
    
    Args:
        question_id: ID of the question
        num_answers: Number of incorrect answers to generate
        debug_mode: Enable verbose debug output
        incorrect_answer_service: Incorrect answer service dependency
        question_service: Question service dependency
        
    Returns:
        Generated incorrect answers
    """
    # Ensure question_id is a valid UUID string
    question_id = ensure_uuid(question_id)
    
    # Get the question
    question = await question_service.question_repository.get_by_id(question_id)
    
    if not question:
        raise HTTPException(
            status_code=404,
            detail=f"Question with ID {question_id} not found"
        )
    
    # Generate incorrect answers
    result = await incorrect_answer_service.generate_and_store_incorrect_answers(
        questions=[question],
        num_incorrect_answers=num_answers,
        debug_mode=debug_mode
    )
    
    # Check if we got results
    if question_id in result:
        return {"question_id": question_id, "incorrect_answers": result[question_id]}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate incorrect answers"
        )

# FIXED: Changed route path to avoid duplication with base prefix
@router.post("/incorrect-answers/batch")
async def generate_pack_incorrect_answers(
    pack_id: str = Path(..., description="ID of the pack"),
    num_answers: int = Query(3, ge=1, le=10, description="Number of incorrect answers per question"),
    batch_size: int = Query(5, ge=1, le=20, description="Batch size for processing"),
    debug_mode: bool = Query(False, description="Enable verbose debug output"),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service),
    pack_service: PackService = Depends(get_pack_service)
):
    """
    Generate incorrect answers for all questions in a pack.
    
    Args:
        pack_id: ID of the pack
        num_answers: Number of incorrect answers per question
        batch_size: Batch size for processing
        debug_mode: Enable verbose debug output
        incorrect_answer_service: Incorrect answer service dependency
        pack_service: Pack service dependency
        
    Returns:
        Status of incorrect answer generation
    """
    # Ensure pack_id is a valid UUID string
    pack_id = ensure_uuid(pack_id)
    
    # Verify the pack exists
    pack_repo = pack_service.pack_repository
    pack = await pack_repo.get_by_id(pack_id)
    
    if not pack:
        raise HTTPException(
            status_code=404,
            detail=f"Pack with ID {pack_id} not found"
        )
    
    # Generate incorrect answers for all questions in the pack
    results = await incorrect_answer_service.generate_for_pack(
        pack_id=pack_id,
        num_incorrect_answers=num_answers,
        batch_size=batch_size,
        debug_mode=debug_mode
    )
    
    return {
        "pack_id": pack_id,
        "questions_processed": len(results),
        "status": "completed"
    }