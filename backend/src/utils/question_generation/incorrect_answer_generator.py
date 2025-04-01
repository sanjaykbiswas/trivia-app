# backend/src/utils/question_generation/incorrect_answer_generator.py
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import time
import math # Import math for ceiling

from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text
from ..llm.llm_parsing_utils import parse_json_from_llm
from ...models.question import Question

logger = logging.getLogger(__name__)

# --- Define Custom Exception ---
class IncorrectAnswerGenerationError(Exception):
    """Custom exception for failures in generating incorrect answers."""
    def __init__(self, message: str, failed_question_ids: List[str]):
        self.message = message
        self.failed_question_ids = failed_question_ids
        super().__init__(f"{message} Failed for question IDs: {', '.join(failed_question_ids)}")
# --- End Custom Exception ---

class IncorrectAnswerGenerator:
    """
    Generates plausible but incorrect answers for trivia questions,
    with a retry mechanism using smaller batches for failures.
    Raises an error if generation fails for any question after retries.
    """
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service or LLMService()
        self.debug_enabled = False

    async def generate_incorrect_answers(
        self,
        questions: List[Question],
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        max_retries: int = 1, # If > 0, allows one retry attempt with smaller batches
        debug_mode: bool = False
    ) -> List[Tuple[str, List[str]]]:
        """
        Generate incorrect answers for a list of questions with retries.

        Args:
            questions: List of Question objects.
            num_incorrect_answers: Number of incorrect answers per question.
            batch_size: Initial number of questions per LLM call.
            max_retries: If > 0, allows one retry attempt with a smaller batch size.
            debug_mode: Enable verbose debug output.

        Returns:
            List of tuples (question_id, incorrect_answers_list). Contains entries
            only for questions where generation was successful.

        Raises:
            IncorrectAnswerGenerationError: If answers could not be generated for
                                            one or more questions after all attempts.
        """
        self.debug_enabled = debug_mode
        if not questions:
            logger.warning("No questions provided for incorrect answer generation")
            return []

        all_results_map: Dict[str, List[str]] = {}
        original_question_map = {q.id: q for q in questions}
        original_question_ids = set(original_question_map.keys())

        questions_to_process = list(questions)

        # --- Initial Attempt ---
        initial_batches = [questions_to_process[i:i + batch_size] for i in range(0, len(questions_to_process), batch_size)]
        if self.debug_enabled:
             print(f"\nProcessing {len(questions_to_process)} questions in {len(initial_batches)} initial batches (size {batch_size})")

        tasks = []
        for batch_idx, batch in enumerate(initial_batches):
            if self.debug_enabled:
                print(f"  Creating task for Initial Batch {batch_idx+1}/{len(initial_batches)} ({len(batch)} questions)")
            task = asyncio.create_task(
                self._process_batch(batch, num_incorrect_answers, batch_idx, len(initial_batches), is_retry=False)
            )
            tasks.append(task)

        initial_batch_results = await asyncio.gather(*tasks)

        for batch_answers in initial_batch_results:
            for q_id, answers in batch_answers:
                if q_id not in all_results_map:
                     all_results_map[q_id] = answers

        # --- Identify Failures from Initial Attempt ---
        currently_failed_ids = original_question_ids - set(all_results_map.keys())
        failed_questions = [original_question_map[q_id] for q_id in currently_failed_ids]

        if self.debug_enabled:
            print(f"Initial attempt finished. Successful: {len(all_results_map)}. Failed: {len(failed_questions)}.")

        # --- Retry Attempt (if applicable and failures exist) ---
        if failed_questions and max_retries > 0:
            retry_batch_size = max(1, math.ceil(batch_size / 2))
            logger.warning(f"Retrying generation for {len(failed_questions)} failed questions with smaller batch size {retry_batch_size}")

            retry_batches = [failed_questions[i:i + retry_batch_size] for i in range(0, len(failed_questions), retry_batch_size)]
            if self.debug_enabled:
                 print(f"\nProcessing {len(failed_questions)} failed questions in {len(retry_batches)} retry batches (size {retry_batch_size})")

            retry_tasks = []
            for batch_idx, batch in enumerate(retry_batches):
                if self.debug_enabled:
                    print(f"  Creating task for Retry Batch {batch_idx+1}/{len(retry_batches)} ({len(batch)} questions)")
                task = asyncio.create_task(
                    self._process_batch(batch, num_incorrect_answers, batch_idx, len(retry_batches), is_retry=True)
                )
                retry_tasks.append(task)

            retry_batch_results = await asyncio.gather(*retry_tasks)

            processed_in_retry = 0
            for batch_answers in retry_batch_results:
                for q_id, answers in batch_answers:
                    if q_id not in all_results_map:
                         all_results_map[q_id] = answers
                         processed_in_retry += 1

            # Update the list of failures after the retry
            currently_failed_ids = original_question_ids - set(all_results_map.keys())

            if self.debug_enabled:
                 print(f"Retry attempt finished. Successful in retry: {processed_in_retry}. Still failed: {len(currently_failed_ids)}.")


        # --- Final Check and Error Handling (No Fallbacks) ---
        final_failed_ids = list(original_question_ids - set(all_results_map.keys()))

        if final_failed_ids:
            error_msg = f"Failed to generate incorrect answers for {len(final_failed_ids)} questions after {max_retries+1} attempts."
            logger.error(error_msg + f" Failed IDs: {final_failed_ids}")
            # Raise the custom error instead of generating fallbacks
            raise IncorrectAnswerGenerationError(error_msg, final_failed_ids)
        else:
            # All questions succeeded, format the results
            final_results = [(q_id, all_results_map[q_id]) for q_id in original_question_map.keys() if q_id in all_results_map] # Maintain order if possible
            # Ensure the final list matches the original count - should be guaranteed if no error raised
            if len(final_results) != len(questions):
                 logger.error(f"Mismatch in final result count ({len(final_results)}) vs original question count ({len(questions)}). This shouldn't happen if no error was raised.")
                 # Fallback to map just in case:
                 final_results = list(all_results_map.items())


            if self.debug_enabled:
                print(f"\nFinal Generation Summary:")
                print(f"  Total Questions: {len(questions)}")
                print(f"  Successfully Generated: {len(final_results)}")
                print(f"  Used Fallbacks: 0 (Error raised on failure)")

            return final_results

    # _process_batch, _build_incorrect_answers_prompt, _parse_and_match_response,
    # _validate_llm_answer_format methods remain unchanged from the previous version.
    # _generate_fallback_incorrect_answers and _generate_fallback_for_batch are kept
    # but should no longer be called by generate_incorrect_answers.

    async def _process_batch(
        self,
        questions_batch: List[Question],
        num_incorrect_answers: int,
        batch_idx: int,
        total_batches: int,
        is_retry: bool = False
    ) -> List[Tuple[str, List[str]]]:
        """
        Process a single batch, returning results ONLY for successes in this call.
        Does NOT generate fallbacks here.
        """
        batch_prefix = "Retry Batch" if is_retry else "Batch"
        logger.info(f"Processing {batch_prefix} {batch_idx+1}/{total_batches} ({len(questions_batch)} questions)")

        question_data_for_prompt = []
        original_questions_map = {}
        for q in questions_batch:
             question_data_for_prompt.append({
                  "id": q.id,
                  "question": q.question,
                  "answer": q.answer
             })
             original_questions_map[q.question] = q

        prompt = self._build_incorrect_answers_prompt(question_data_for_prompt, num_incorrect_answers)

        try:
            raw_response = self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.7, # Consider slightly higher temp for retries?
                max_tokens=2000
            )

            if self.debug_enabled:
                print(f"\n  === Raw LLM Response ({batch_prefix} {batch_idx+1}) ===")
                print(f"  {raw_response[:500]}" + ("..." if len(raw_response) > 500 else ""))
                print("  ===================================\n")

            # Parse and match, returning only successful matches from THIS response
            # Do not generate fallbacks at this stage.
            batch_results = await self._parse_and_match_response(
                response=raw_response,
                original_questions_map=original_questions_map
            )
            return batch_results

        except Exception as e:
            logger.error(f"Error processing {batch_prefix} {batch_idx+1}: {str(e)}")
            if self.debug_enabled:
                print(f"  Error processing {batch_prefix} {batch_idx+1}: {str(e)}")
            return [] # Return empty list on error for this batch


    def _build_incorrect_answers_prompt(
        self,
        question_data: List[Dict[str, Any]], # Now includes ID
        num_incorrect_answers: int
    ) -> str:
        """
        Build the prompt for incorrect answer generation.
        """
        prompt = f"""Generate {num_incorrect_answers} plausible but incorrect answers for each of the following trivia questions.

For each question, I'll provide:
- A unique question_id
- The question text
- The correct answer

Your task is to create {num_incorrect_answers} incorrect answers that meet the guidelines provided previously.

Here are the questions (pay attention to the question_id):
"""
        for item in question_data:
            # Basic escaping for JSON within the prompt string
            q_text = item['question'].replace('"', '\\"')
            c_ans = item['answer'].replace('"', '\\"')
            prompt += f"""
{{
  "question_id": "{item['id']}",
  "question": "{q_text}",
  "correct_answer": "{c_ans}"
}}
"""
        prompt += f"""
Return your response as a valid JSON array containing objects. Each object MUST have these EXACT keys:
- "question_id": The EXACT unique ID provided for the question above.
- "question": The EXACT original question text provided above.
- "incorrect_answers": An array of {num_incorrect_answers} strings representing the generated incorrect answers.

Example of the required output structure:
[
  {{
    "question_id": "uuid-for-question-1",
    "question": "What is the capital of France?",
    "incorrect_answers": ["London", "Rome", "Berlin"]
  }},
  {{
    "question_id": "uuid-for-question-2",
    "question": "Which planet is known as the Red Planet?",
    "incorrect_answers": ["Venus", "Jupiter", "Saturn"]
  }}
  // ... more objects following the same structure
]

IMPORTANT NOTES:
- Use the EXACT question_id provided for each question in your response.
- Include the EXACT original question text in the "question" field of your response.
- Provide exactly {num_incorrect_answers} incorrect answers per question.
- DO NOT include the correct answer in the incorrect answers list.
- Ensure all incorrect answers are factually wrong.
- Return ONLY the JSON array without any additional text or markdown formatting.
- Ensure the final output is a single, valid JSON array.
"""
        return prompt

    async def _parse_and_match_response(
        self,
        response: str,
        original_questions_map: Dict[str, Question] # Map: original question text -> Question object
    ) -> List[Tuple[str, List[str]]]:
        """
        Parses the LLM response and matches items to original questions.
        Returns only successfully matched items from this specific response.
        """
        parsed_data = await parse_json_from_llm(response, []) # Default to empty list

        if self.debug_enabled:
            print(f"    Parsing LLM Response Chunk:")
            print(f"    Type: {type(parsed_data)}")

        # Inlined Logic from ensure_list_structure
        answers_data_list: List = []
        if isinstance(parsed_data, list):
            answers_data_list = parsed_data
        elif isinstance(parsed_data, dict):
            found = False
            common_list_keys = ['questions', 'answers', 'items', 'results', 'data', 'list', 'response', 'content', 'entities']
            for key in common_list_keys:
                if key in parsed_data and isinstance(parsed_data[key], list):
                    answers_data_list = parsed_data[key]
                    logger.debug(f"Extracted list from dictionary key: '{key}'")
                    found = True
                    break
            if not found and len(parsed_data) == 1:
                 first_value = next(iter(parsed_data.values()))
                 if isinstance(first_value, list):
                     answers_data_list = first_value
                     logger.debug("Extracted list from single-item dictionary's value")
                     found = True
            if not found:
                 logger.warning(f"Could not find list within parsed dict. Wrapping dict in list.")
                 answers_data_list = [parsed_data]
        elif parsed_data is not None:
             logger.warning(f"Parsed data was not list or dict ({type(parsed_data)}). Wrapping in list.")
             answers_data_list = [parsed_data]
        else:
             logger.warning("Parsed data was None. Using empty list.")
             answers_data_list = []
        # End Inlined Logic

        validated_answers_data = self._validate_llm_answer_format(answers_data_list)

        results = []
        processed_ids_in_this_response = set()

        for item in validated_answers_data:
            question_id_from_llm = item.get("question_id")
            question_text_from_llm = item.get("question")
            incorrect_answers = item.get("incorrect_answers", [])
            target_question: Optional[Question] = None

            # Matching Logic (ID first, then Text)
            if question_id_from_llm:
                found_by_id = False
                for q_obj in original_questions_map.values():
                    if q_obj.id == question_id_from_llm:
                        target_question = q_obj
                        found_by_id = True
                        break
            if not target_question and question_text_from_llm:
                if question_text_from_llm in original_questions_map:
                    target_question = original_questions_map[question_text_from_llm]
                else:
                    normalized_llm_text = clean_text(question_text_from_llm).lower()
                    for original_text, q_obj in original_questions_map.items():
                        normalized_original_text = clean_text(original_text).lower()
                        if normalized_llm_text == normalized_original_text:
                            target_question = q_obj
                            break

            if target_question:
                if target_question.id in processed_ids_in_this_response:
                    continue

                if isinstance(incorrect_answers, list) and all(isinstance(a, str) for a in incorrect_answers):
                    cleaned_answers = [clean_text(a) for a in incorrect_answers if a]
                    correct_answer_lower = target_question.answer.lower()
                    filtered_answers = [a for a in cleaned_answers if clean_text(a).lower() != correct_answer_lower]

                    if filtered_answers:
                        results.append((target_question.id, filtered_answers))
                        processed_ids_in_this_response.add(target_question.id)
                else:
                    logger.warning(f"Invalid incorrect_answers format from LLM for QID {target_question.id}")

        if self.debug_enabled:
            print(f"    Successfully parsed and matched {len(results)} items from this LLM response.")

        return results

    def _validate_llm_answer_format(self, answers: List) -> List[Dict]:
        """Validate and clean answer list format received from LLM."""
        result = []
        for a in answers:
            if not isinstance(a, dict):
                logger.warning(f"Skipping non-dict item in LLM answer response: {type(a)}")
                continue
            has_id = "question_id" in a
            has_text = "question" in a and isinstance(a["question"], str)
            has_answers = "incorrect_answers" in a and isinstance(a["incorrect_answers"], list)
            if (has_id or has_text) and has_answers:
                result.append(a)
            else:
                 logger.warning(f"Skipping item with missing/invalid keys in LLM response: {a}")
        return result