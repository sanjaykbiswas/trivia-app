# backend/src/api/routes/question.py
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from typing import Optional, List, Any
import logging
import traceback # Import traceback for detailed error logging

from ..dependencies import (
    get_question_service,
    get_seed_question_service,
    get_difficulty_service,
    get_pack_service,
    get_incorrect_answer_service # Make sure this is imported
)
from ..schemas import (
    QuestionGenerateRequest, SeedQuestionRequest, SeedQuestionTextRequest,
    QuestionResponse, QuestionsResponse, SeedQuestionsResponse,
    CustomInstructionsGenerateRequest, CustomInstructionsInputRequest, CustomInstructionsResponse,
    BatchQuestionGenerateRequest, BatchQuestionGenerateResponse # Import new schemas
)
from ...services.question_service import QuestionService
from ...services.seed_question_service import SeedQuestionService
from ...services.difficulty_service import DifficultyService
from ...services.pack_service import PackService
from ...services.incorrect_answer_service import IncorrectAnswerService, IncorrectAnswerGenerationError # Make sure this is imported and the custom error
from ...models.question import DifficultyLevel, Question # Import Question model
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
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service) # Add dependency
):
    """
    Generate trivia questions for a SINGLE pack topic and generate incorrect answers.
    """
    pack_id_uuid = ensure_uuid(pack_id)

    # 1. Verify Pack Exists
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        # 2. Generate Questions for the single topic
        # Note: The service method now returns the created Question objects
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
                     num_incorrect_answers=3, # Or get from config/request
                     batch_size=5, # Or get from config/request
                     debug_mode=question_request.debug_mode
                 )
                logger.info(f"Incorrect answer generation complete for topic '{question_request.pack_topic}'.")
            except IncorrectAnswerGenerationError as ia_error:
                 # Log the specific error but don't fail the whole request,
                 # return the questions that were successfully created.
                 logger.error(f"Failed to generate some incorrect answers for topic '{question_request.pack_topic}': {ia_error.message}")
                 # Optionally add a warning header or field to the response later if needed
            except Exception as e_ia:
                 logger.error(f"Unexpected error during incorrect answer generation for topic '{question_request.pack_topic}': {e_ia}", exc_info=True)
                 # Decide if this should fail the request or just warn
        else:
             logger.warning(f"No questions were generated for topic '{question_request.pack_topic}', skipping incorrect answer generation.")


        # 4. Format response (use the created_questions list)
        # Convert Question objects to QuestionResponse objects for the API response
        response_questions = [
            QuestionResponse.model_validate(q) for q in created_questions
        ]

        return QuestionsResponse(
            total=len(response_questions),
            questions=response_questions
        )

    except Exception as e:
        logger.error(f"Error generating questions for topic '{question_request.pack_topic}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )


# --- Batch Question Generation Endpoint ---

@router.post("/batch-generate", response_model=BatchQuestionGenerateResponse)
async def batch_generate_questions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: BatchQuestionGenerateRequest = Body(...),
    question_service: QuestionService = Depends(get_question_service),
    pack_service: PackService = Depends(get_pack_service),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service)
):
    """
    Generate questions for multiple topics within a pack concurrently,
    followed by batch incorrect answer generation for all newly created questions.
    """
    pack_id_uuid = ensure_uuid(pack_id)

    # 1. Verify Pack Exists
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    batch_results: Dict[str, Any] = {}
    final_status = "completed"
    error_list = []

    try:
        # 2. Call the batch question generation service method
        batch_results = await question_service.batch_generate_and_store_questions(
            pack_id=pack_id_uuid,
            creation_name=pack.name,
            topic_configs=request.topic_configs,
            debug_mode=request.debug_mode
            # Pass global_custom_instructions if added to schema/service
        )
        error_list.extend(batch_results.get("failed_topics", [])) # Add initial failures

    except Exception as e_qg:
        logger.error(f"Core batch question generation failed for pack {pack_id}: {str(e_qg)}", exc_info=True)
        # If the core batch generation fails catastrophically, we likely have no questions
        final_status = "failed"
        error_list = [config.topic for config in request.topic_configs] # Mark all as failed
        # Return summary immediately
        return BatchQuestionGenerateResponse(
            pack_id=pack_id,
            topics_processed=[],
            total_questions_generated=0,
            status=final_status,
            errors=error_list
        )

    # 3. Trigger Incorrect Answer Generation for ALL newly created questions from the batch
    newly_generated_questions: List[Question] = batch_results.get("generated_questions", [])
    if newly_generated_questions:
         logger.info(f"Batch question generation step complete. Triggering incorrect answer generation for {len(newly_generated_questions)} new questions...")
         try:
             await incorrect_answer_service.generate_and_store_incorrect_answers(
                 questions=newly_generated_questions, # Pass the list of Question objects
                 num_incorrect_answers=3, # Or get from config/request
                 batch_size=5, # Or get from config/request
                 debug_mode=request.debug_mode
             )
             logger.info("Incorrect answer generation for batch completed.")
         except IncorrectAnswerGenerationError as ia_error:
             # Log the error and potentially update the status/errors
             logger.error(f"Partial failure during incorrect answer generation for batch in pack {pack_id}: {ia_error.message}")
             # Add the failed question IDs' topics to the error list if possible (might require mapping back)
             # For simplicity, we might just indicate a partial failure status
             final_status = "partial_failure" # Mark overall status as partial
             # You could try to find which topics these questions belong to and add to error_list
             # error_list.extend(find_topics_for_failed_questions(ia_error.failed_question_ids, newly_generated_questions))
         except Exception as e_ia:
             logger.error(f"Unexpected error during batch incorrect answer generation for pack {pack_id}: {e_ia}", exc_info=True)
             final_status = "partial_failure" # Mark as partial failure due to IA error

    else:
         logger.warning("No new questions were generated in the batch, skipping incorrect answer generation.")


    # 4. Determine final status based on both steps
    successful_topics = batch_results.get("success_topics", [])
    failed_topics_qg = batch_results.get("failed_topics", [])

    if not successful_topics and failed_topics_qg:
         final_status = "failed"
    elif failed_topics_qg or final_status == "partial_failure": # If QG failed or IA failed
         final_status = "partial_failure"
    # else: status remains "completed"

    # Ensure error list is unique
    error_list = list(set(failed_topics_qg)) # Start with QG failures

    # Format and return the batch summary response
    return BatchQuestionGenerateResponse(
        pack_id=pack_id,
        topics_processed=successful_topics,
        total_questions_generated=batch_results.get("total_generated", 0),
        status=final_status,
        errors=error_list if error_list else None
    )


# --- Other existing endpoints (/get, /seed, /custom-instructions, /incorrect-answers) ---

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

# Custom Instructions Endpoints
@router.post("/custom-instructions/generate", response_model=CustomInstructionsResponse)
async def generate_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsGenerateRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        custom_instructions = await seed_question_service.generate_custom_instructions(
            pack_id=pack_id_uuid,
            pack_topic=request.pack_topic
        )
        if custom_instructions is None:
            raise HTTPException(status_code=500, detail="Failed to generate custom instructions")
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    except Exception as e:
        logger.error(f"Error generating custom instructions for pack {pack_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating custom instructions: {str(e)}")


@router.post("/custom-instructions/input", response_model=CustomInstructionsResponse)
async def input_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    request: CustomInstructionsInputRequest = Body(...),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        success = await seed_question_service.process_and_store_manual_instructions(
            pack_id=pack_id_uuid,
            instructions=request.instructions
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store custom instructions")

        stored_instructions = await seed_question_service.get_custom_instructions(pack_id_uuid)
        return CustomInstructionsResponse(custom_instructions=stored_instructions)
    except Exception as e:
        logger.error(f"Error processing custom instructions for pack {pack_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing custom instructions: {str(e)}")


@router.get("/custom-instructions", response_model=CustomInstructionsResponse)
async def get_custom_instructions(
    pack_id: str = Path(..., description="ID of the pack"),
    seed_question_service: SeedQuestionService = Depends(get_seed_question_service),
    pack_service: PackService = Depends(get_pack_service)
):
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        custom_instructions = await seed_question_service.get_custom_instructions(pack_id_uuid)
        return CustomInstructionsResponse(custom_instructions=custom_instructions)
    except Exception as e:
        logger.error(f"Error retrieving custom instructions for pack {pack_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving custom instructions: {str(e)}")

# Incorrect Answers Endpoints
@router.post("/{question_id}/incorrect-answers")
async def generate_single_question_incorrect_answers(
    pack_id: str = Path(..., description="ID of the pack"), # Keep pack_id for consistency
    question_id: str = Path(..., description="ID of the question"),
    num_answers: int = Query(3, ge=1, le=10, description="Number of incorrect answers to generate"),
    debug_mode: bool = Query(False, description="Enable verbose debug output"),
    incorrect_answer_service: IncorrectAnswerService = Depends(get_incorrect_answer_service),
    question_service: QuestionService = Depends(get_question_service)
):
    """
    Generate incorrect answers for a specific question within a pack.
    """
    question_id_uuid = ensure_uuid(question_id)
    pack_id_uuid = ensure_uuid(pack_id) # Ensure pack_id is also UUID str

    # Verify question exists and belongs to the pack
    question = await question_service.question_repository.get_by_id(question_id_uuid)
    if not question:
        raise HTTPException(status_code=404, detail=f"Question with ID {question_id} not found")
    if str(question.pack_id) != pack_id_uuid: # Compare UUID strings
         raise HTTPException(status_code=400, detail=f"Question {question_id} does not belong to pack {pack_id}")

    try:
        result_map = await incorrect_answer_service.generate_and_store_incorrect_answers(
            questions=[question], # Pass as a list
            num_incorrect_answers=num_answers,
            debug_mode=debug_mode
        )

        # The service method now returns a map of ID -> answers
        if question_id_uuid in result_map:
             # Return the ID as string in the response
            return {"question_id": str(question_id_uuid), "incorrect_answers": result_map[question_id_uuid]}
        else:
             # This might happen if the generator failed and the service handled it
             logger.warning(f"Incorrect answers might not have been generated/stored successfully for question {question_id}")
             raise HTTPException(status_code=500, detail="Failed to generate or store incorrect answers")
    except IncorrectAnswerGenerationError as ia_error:
        logger.error(f"Incorrect answer generation failed definitively for question {question_id}: {ia_error.message}")
        raise HTTPException(status_code=500, detail=f"Failed to generate incorrect answers: {ia_error.message}")
    except Exception as e:
        logger.error(f"Error generating incorrect answers for question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate incorrect answers: {str(e)}")


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
    Generate incorrect answers for ALL questions currently in a pack.
    """
    pack_id_uuid = ensure_uuid(pack_id)
    pack = await pack_service.pack_repository.get_by_id(pack_id_uuid)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack with ID {pack_id} not found")

    try:
        results_map = await incorrect_answer_service.generate_for_pack(
            pack_id=pack_id_uuid,
            num_incorrect_answers=num_answers,
            batch_size=batch_size,
            debug_mode=debug_mode
        )
        # The service method now returns a map {question_id: [answers]}

        return {
            "pack_id": pack_id,
            "questions_processed": len(results_map), # Count successful ones
            "status": "completed" # Or determine based on potential partial failures if service indicates it
        }
    except IncorrectAnswerGenerationError as e:
         logger.error(f"Partial failure generating incorrect answers for pack {pack_id}: {e.message}")
         # Return a specific status indicating partial success
         return {
            "pack_id": pack_id,
            "questions_processed": -1, # Indicate partial failure or count successes if known
            "status": "partial_failure",
            "error": e.message,
            "failed_ids": e.failed_question_ids
         }
    except Exception as e:
        logger.error(f"Error generating incorrect answers for pack {pack_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate incorrect answers for pack: {str(e)}")