# backend/src/api/routes/question.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Optional, List, Any, Dict # Added Dict
import logging
import traceback

from ..dependencies import (
    get_question_service,
    get_seed_question_service,
    get_difficulty_service,
    get_pack_service,
    get_incorrect_answer_service
)
from ..schemas import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse,
    CustomInstructionsGenerateRequest, CustomInstructionsInputRequest, CustomInstructionsResponse,
    # --- Use the updated schemas ---
    BatchQuestionGenerateRequest, BatchQuestionGenerateResponse
)
from ...services.question_service import QuestionService
from ...services.seed_question_service import SeedQuestionService
from ...services.difficulty_service import DifficultyService
from ...services.pack_service import PackService
from ...services.incorrect_answer_service import IncorrectAnswerService, IncorrectAnswerGenerationError
from ...models.question import DifficultyLevel, Question
from ...utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# --- Single Topic Question Generation Endpoint ---
@router.post("/", response_model=QuestionsResponse)
async def generate_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    question_request: QuestionGenerateRequest = Body(...),
    question_service: QuestionService = Depends(get_question_service),
    pack_service: PackService = Depends(get_pack_service),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service)
):
    """
    Generate trivia questions for a SINGLE pack topic/difficulty and generate incorrect answers.
    """
    pack_id_uuid = ensure_uuid(pack_id)

    # 1. Verify Pack Exists
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # 2. Generate Questions for the single topic/difficulty
        created_questions: List[Question] = await question_service.generate_and_store_questions(
            pack_id=pack_id_uuid,
            creation_name=pack.name,
            pack_topic=question_request.pack_topic,
            difficulty=question_request.difficulty,
            num_questions=question_request.num_questions,
            debug_mode=question_request.debug_mode,
            custom_instructions=question_request.custom_instructions
        )

        # 3. Generate Incorrect Answers for the newly created questions
        if created_questions:
            logger.info(f"Generated {len(created_questions)} questions for topic '{question_request.pack_topic}'. Now generating incorrect answers...")
            try:
                await incorrect_answer_service.generate_and_store_incorrect_answers(
                     questions=created_questions,
                     num_incorrect_answers=3,
                     batch_size=5,
                     debug_mode=question_request.debug_mode
                 )
                logger.info(f"Incorrect answer generation complete for topic '{question_request.pack_topic}'.")
            except IncorrectAnswerGenerationError as ia_error:
                 logger.error(f"Failed to generate some incorrect answers for topic '{question_request.pack_topic}': {ia_error.message}")
            except Exception as e_ia:
                 logger.error(f"Unexpected error during incorrect answer generation for topic '{question_request.pack_topic}': {e_ia}", exc_info=True)
        else:
             logger.warning(f"No questions were generated for topic '{question_request.pack_topic}', skipping incorrect answer generation.")

        # 4. Format response
        response_questions = [ QuestionResponse.model_validate(q) for q in created_questions ]
        return QuestionsResponse( total=len(response_questions), questions=response_questions )

    except Exception as e:
        logger.error(f"Error generating single topic questions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


# --- Batch Question Generation Endpoint (MODIFIED Result Handling) ---
@router.post("/batch-generate", response_model=BatchQuestionGenerateResponse)
async def batch_generate_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: BatchQuestionGenerateRequest = Body(...), # Uses updated schema
    question_service: QuestionService = Depends(get_question_service),
    pack_service: PackService = Depends(get_pack_service),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service)
):
    """
    Generate questions for multiple topics *and* difficulties within a pack concurrently,
    followed by batch incorrect answer generation for all newly created questions.
    """
    pack_id_uuid = ensure_uuid(pack_id)

    # 1. Verify Pack Exists (remains the same)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    batch_results: Dict[str, Any] = {}
    final_status = "completed" # Default status
    # Simplifed error list (just topic names where *any* difficulty failed)
    error_list: List[str] = []

    try:
        # 2. Call the batch question generation service method
        batch_results = await question_service.batch_generate_and_store_questions(
            pack_id=pack_id_uuid,
            creation_name=pack.name,
            topic_configs=request.topic_configs, # Pass the new structure
            debug_mode=request.debug_mode
        )
        error_list.extend(batch_results.get("failed_topics", [])) # Get simplified list of failed topics

    except Exception as e_qg:
        # Handle catastrophic failure during generation
        logger.error(f"Core batch question generation failed for pack {pack_id}: {str(e_qg)}", exc_info=True)
        final_status = "failed"
        error_list = list(set([tc.topic for tc in request.topic_configs]))
        return BatchQuestionGenerateResponse(
            pack_id=pack_id, topics_processed=[], total_questions_generated=0,
            status=final_status, errors=error_list
        )

    # 3. Trigger Incorrect Answer Generation
    newly_generated_questions: List[Question] = batch_results.get("generated_questions", [])
    if newly_generated_questions:
         logger.info(f"Batch question step complete. Triggering incorrect answers for {len(newly_generated_questions)} new questions...")
         try:
             await incorrect_answer_service.generate_and_store_incorrect_answers(
                 questions=newly_generated_questions, num_incorrect_answers=3, batch_size=5, debug_mode=request.debug_mode
             )
             logger.info("Incorrect answer generation for batch completed.")
         except IncorrectAnswerGenerationError as ia_error:
             logger.error(f"Partial failure during incorrect answer generation for batch in pack {pack_id}: {ia_error.message}")
             final_status = "partial_failure"
             failed_q_ids_set = set(ia_error.failed_question_ids)
             failed_ia_topics = {q.pack_topics_item for q in newly_generated_questions if q.id in failed_q_ids_set and q.pack_topics_item}
             error_list.extend(list(failed_ia_topics))
         except Exception as e_ia:
             logger.error(f"Unexpected error during batch incorrect answer generation for pack {pack_id}: {e_ia}", exc_info=True)
             final_status = "partial_failure"
    else:
         logger.warning("No new questions generated in the batch, skipping incorrect answer generation.")


    # 4. Determine final status and return summary
    successful_topics = batch_results.get("topics_processed", [])
    failed_topics_qg = batch_results.get("failed_topics", [])
    if final_status != "partial_failure":
        if not successful_topics and failed_topics_qg: final_status = "failed"
        elif failed_topics_qg: final_status = "partial_failure"

    unique_error_topics = list(set(error_list))
    return BatchQuestionGenerateResponse(
        pack_id=pack_id, topics_processed=successful_topics,
        total_questions_generated=batch_results.get("total_generated", 0),
        status=final_status, errors=unique_error_topics if unique_error_topics else None
    )
# --- END Batch Endpoint ---


# --- Other existing endpoints (Added Back In) ---

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
    """
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # Get questions based on filters
        if topic:
            questions = await question_service.get_questions_by_topic(pack_id_uuid, topic)
        else:
            questions = await question_service.get_questions_by_pack_id(pack_id_uuid)

        # Filter by difficulty if provided
        if difficulty:
            questions = [q for q in questions if q.difficulty_current == difficulty]

        # Apply pagination
        total = len(questions)
        paginated_questions_data = questions[skip:skip + limit]

        # Convert Question models to QuestionResponse models
        response_questions = [
             QuestionResponse.model_validate(q) for q in paginated_questions_data
        ]

        return QuestionsResponse(
            total=total,
            questions=response_questions
        )

    except Exception as e:
        logger.error(f"Error retrieving questions for pack {pack_id}: {str(e)}", exc_info=True)
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
    """
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        pack_creation_data = await seed_question_service.pack_creation_repository.get_by_pack_id(pack_id_uuid)
        if not pack_creation_data:
            # Ensure pack creation data exists before storing seeds
            from ...models.pack_creation_data import PackCreationDataCreate
            creation_data = PackCreationDataCreate(
                pack_id=pack_id_uuid,
                creation_name=pack.name,
                pack_topics=[] # Initialize topics
            )
            await seed_question_service.pack_creation_repository.create(obj_in=creation_data)

        success = await seed_question_service.store_seed_questions(
            pack_id=pack_id_uuid,
            seed_questions=seed_request.seed_questions
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store seed questions")

        return SeedQuestionsResponse(
            count=len(seed_request.seed_questions),
            seed_questions=seed_request.seed_questions
        )

    except Exception as e:
        logger.error(f"Error storing seed questions for pack {pack_id}: {str(e)}", exc_info=True)
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
    """
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        extracted_questions = await seed_question_service.seed_processor.detect_and_process_input(
            text_request.text_content
        )

        if not extracted_questions:
            raise HTTPException(status_code=400, detail="No questions could be extracted")

        pack_creation_data = await seed_question_service.pack_creation_repository.get_by_pack_id(pack_id_uuid)
        if not pack_creation_data:
            from ...models.pack_creation_data import PackCreationDataCreate
            creation_data = PackCreationDataCreate(pack_id=pack_id_uuid, creation_name=pack.name, pack_topics=[])
            await seed_question_service.pack_creation_repository.create(obj_in=creation_data)

        success = await seed_question_service.store_seed_questions(
            pack_id=pack_id_uuid,
            seed_questions=extracted_questions
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to store extracted seed questions")

        return SeedQuestionsResponse(
            count=len(extracted_questions),
            seed_questions=extracted_questions
        )

    except Exception as e:
        logger.error(f"Error extracting seed questions for pack {pack_id}: {str(e)}", exc_info=True)
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
    """
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        seed_questions = await seed_question_service.get_seed_questions(pack_id_uuid)
        return SeedQuestionsResponse(
            count=len(seed_questions),
            seed_questions=seed_questions
        )
    except Exception as e:
        logger.error(f"Error retrieving seed questions for pack {pack_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving seed questions: {str(e)}"
        )

# Custom Instructions Endpoints (remain unchanged)
@router.post("/custom-instructions/generate", response_model=CustomInstructionsResponse)
async def generate_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsGenerateRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack: raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")
    try:
        custom_instructions = await seed_question_service.generate_custom_instructions(pack_id_uuid, request.pack_topic)
        if custom_instructions is None: raise HTTPException(status_code=500, detail="Failed to generate instructions")
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    except Exception as e:
        logger.error(f"Error generating custom instructions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.post("/custom-instructions/input", response_model=CustomInstructionsResponse)
async def input_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsInputRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack: raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")
    try:
        success = await seed_question_service.process_and_store_manual_instructions(pack_id_uuid, request.instructions)
        if not success: raise HTTPException(status_code=500, detail="Failed to store instructions")
        stored_instructions = await seed_question_service.get_custom_instructions(pack_id_uuid)
        return CustomInstructionsResponse(custom_instructions=stored_instructions)
    except Exception as e:
        logger.error(f"Error processing custom instructions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {e}")


@router.get("/custom-instructions", response_model=CustomInstructionsResponse)
async def get_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack: raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")
    try:
        custom_instructions = await seed_question_service.get_custom_instructions(pack_id_uuid)
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    except Exception as e:
        logger.error(f"Error retrieving custom instructions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Incorrect Answers Endpoints (remain unchanged)
@router.post("/{question_id}/incorrect-answers")
async def generate_single_question_incorrect_answers(
    pack_id: str = Path(..., description="ID of the pack"),
    question_id: str = Path(..., description="ID of the question"),
    num_answers: int = Query(3, ge=1, le=10), debug_mode: bool = Query(False),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service),
    question_service: QuestionService = Depends(get_question_service)
):
    question_id_uuid = ensure_uuid(question_id)
    pack_id_uuid = ensure_uuid(pack_id)
    question = await question_service.question_repository.get_by_id(question_id_uuid)
    if not question: raise HTTPException(status_code=404, detail=f"Question {question_id} not found")
    if str(question.pack_id) != pack_id_uuid: raise HTTPException(status_code=400, detail=f"Question {question_id} not in pack {pack_id}")
    try:
        result_map = await incorrect_answer_service.generate_and_store_incorrect_answers(
            questions=[question], num_incorrect_answers=num_answers, debug_mode=debug_mode
        )
        if question_id_uuid in result_map:
            return {"question_id": str(question_id_uuid), "incorrect_answers": result_map[question_id_uuid]}
        else:
            # This case means generation/storage failed definitively within the service
            raise HTTPException(status_code=500, detail="Failed to generate or store incorrect answers for this question.")
    except IncorrectAnswerGenerationError as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate incorrect answers: {e.message}")
    except Exception as e:
        logger.error(f"Error generating incorrect answers for Q {question_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {e}")


@router.post("/incorrect-answers/batch")
async def generate_pack_incorrect_answers(
    pack_id: str = Path(..., description="ID of the pack"),
    num_answers: int = Query(3, ge=1, le=10), batch_size: int = Query(5, ge=1, le=20), debug_mode: bool = Query(False),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack: raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")
    try:
        results_map = await incorrect_answer_service.generate_for_pack(
            pack_id=pack_id_uuid, num_incorrect_answers=num_answers, batch_size=batch_size, debug_mode=debug_mode
        )
        # Success means no exception was raised by the service
        return {"pack_id": pack_id, "questions_processed": len(results_map), "status": "completed"}
    except IncorrectAnswerGenerationError as e:
         # Service layer indicates partial/total failure
         return {
            "pack_id": pack_id, "questions_processed": -1, "status": "partial_failure",
            "error": e.message, "failed_ids": e.failed_question_ids
         }
    except Exception as e:
        logger.error(f"Error generating incorrect answers for pack {pack_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed: {e}")