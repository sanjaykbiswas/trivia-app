# backend/src/utils/question_generation/incorrect_answer_generator.py
"""
Utility for generating incorrect answers for trivia questions using LLM.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio

from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text
from ..llm.llm_parsing_utils import parse_json_from_llm
from ...models.question import Question

# Configure logger
logger = logging.getLogger(__name__)

class IncorrectAnswerGenerator:
    """
    Generates plausible but incorrect answers for trivia questions.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the incorrect answer generator with services.
        
        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()
        self.debug_enabled = False
    
    async def generate_incorrect_answers(
        self,
        questions: List[Question],
        num_incorrect_answers: int = 3,
        batch_size: int = 5,
        debug_mode: bool = False
    ) -> List[Tuple[str, List[str]]]:
        """
        Generate incorrect answers for a list of questions.
        
        Args:
            questions: List of Question objects with correct answers
            num_incorrect_answers: Number of incorrect answers to generate per question
            batch_size: Number of questions to process in each batch
            debug_mode: Enable verbose debug output
            
        Returns:
            List of tuples containing (question_id, incorrect_answers_list)
        """
        self.debug_enabled = debug_mode
        
        if not questions:
            logger.warning("No questions provided for incorrect answer generation")
            return []
        
        # Process questions in batches to avoid overwhelming the LLM
        batches = [questions[i:i + batch_size] for i in range(0, len(questions), batch_size)]
        
        if self.debug_enabled:
            print(f"Processing {len(questions)} questions in {len(batches)} batches")
        
        all_results = []
        
        # Create tasks for each batch to process concurrently
        tasks = []
        for batch_idx, batch in enumerate(batches):
            if self.debug_enabled:
                print(f"Creating task for batch {batch_idx+1}/{len(batches)} ({len(batch)} questions)")
            
            task = asyncio.create_task(
                self._process_batch(batch, num_incorrect_answers, batch_idx, len(batches))
            )
            tasks.append(task)
        
        # Wait for all batch processing to complete
        batch_results = await asyncio.gather(*tasks)
        
        # Combine results from all batches
        for batch_answers in batch_results:
            all_results.extend(batch_answers)
        
        if self.debug_enabled:
            print(f"Generated incorrect answers for {len(all_results)}/{len(questions)} questions")
        
        return all_results
    
    async def _process_batch(
        self, 
        questions_batch: List[Question], 
        num_incorrect_answers: int,
        batch_idx: int, 
        total_batches: int
    ) -> List[Tuple[str, List[str]]]:
        """
        Process a batch of questions to generate incorrect answers.
        
        Args:
            questions_batch: Batch of Question objects
            num_incorrect_answers: Number of incorrect answers to generate per question
            batch_idx: Batch index for logging
            total_batches: Total number of batches
            
        Returns:
            List of tuples containing (question_id, incorrect_answers_list)
        """
        logger.info(f"Processing batch {batch_idx+1}/{total_batches} ({len(questions_batch)} questions)")
        
        # Extract question information for the prompt
        question_data = [
            {
                "id": q.id,
                "question": q.question,
                "answer": q.answer
            }
            for q in questions_batch
        ]
        
        # Generate the prompt for this batch
        prompt = self._build_incorrect_answers_prompt(question_data, num_incorrect_answers)
        
        try:
            # Generate incorrect answers using LLM
            raw_response = self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.7,  # Slightly higher temperature for creativity
                max_tokens=2000   # Ensure enough tokens for multiple answers
            )
            
            if self.debug_enabled:
                print(f"\n=== Raw LLM Response for Batch {batch_idx+1} ===")
                print(raw_response[:1000] + ("..." if len(raw_response) > 1000 else ""))
                print("=================================\n")
            
            # Parse the response to extract incorrect answers
            batch_results = await self._parse_incorrect_answers_response(
                response=raw_response,
                questions=questions_batch
            )
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Error generating incorrect answers for batch {batch_idx+1}: {str(e)}")
            if self.debug_enabled:
                print(f"Error generating incorrect answers for batch {batch_idx+1}: {str(e)}")
            
            # Return empty results for this batch on error
            return [(q.id, []) for q in questions_batch]
    
    def _build_incorrect_answers_prompt(
        self,
        question_data: List[Dict[str, Any]],
        num_incorrect_answers: int
    ) -> str:
        """
        Build the prompt for incorrect answer generation.
        
        Args:
            question_data: List of dictionaries with question information
            num_incorrect_answers: Number of incorrect answers to generate per question
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate {num_incorrect_answers} plausible but incorrect answers for each of the following trivia questions.

For each question, I'll provide:
- The question text
- The correct answer

Your task is to create {num_incorrect_answers} incorrect answers that:
1. Are factually incorrect (the correct answer is already provided)
2. Are plausible and believable to someone with moderate knowledge of the topic
3. Match the same type/category as the correct answer (e.g., if the answer is a city, provide other cities)
4. Follow any constraints in the question (e.g., if asking for "European countries", all answers should be European countries)
5. Vary in difficulty to make the quiz challenging

Here are the questions:
"""
        
        # Add each question and its correct answer to the prompt
        for i, item in enumerate(question_data):
            prompt += f"""
Question {i+1}: {item['question']}
Correct answer: {item['answer']}
"""
        
        # Add formatting instructions
        prompt += f"""
Return your response as a valid JSON array containing objects with this structure:
[
  {{
    "question_id": "id_from_above",
    "incorrect_answers": ["Wrong Answer 1", "Wrong Answer 2", "Wrong Answer 3"]
  }},
  ...
]

IMPORTANT NOTES:
- Provide exactly {num_incorrect_answers} incorrect answers per question
- DO NOT include the correct answer in the incorrect answers list
- Ensure all incorrect answers are factually wrong
- Return ONLY the JSON array without any additional text or markdown formatting
- Ensure each answer is distinct and unique within its question
"""
        
        return prompt
    
    async def _parse_incorrect_answers_response(
        self,
        response: str,
        questions: List[Question]
    ) -> List[Tuple[str, List[str]]]:
        """
        Parse the LLM response to extract incorrect answers.
        
        Args:
            response: Raw response from LLM
            questions: The original questions for fallback
            
        Returns:
            List of tuples containing (question_id, incorrect_answers_list)
        """
        # Create a mapping of question IDs for validation
        question_map = {q.id: q for q in questions}
        
        # Parse the JSON response
        try:
            parsed_data = await parse_json_from_llm(response, [])
            
            if self.debug_enabled:
                print(f"\n=== Parsed Incorrect Answers Data ===")
                print(f"Type: {type(parsed_data)}")
                print(f"Content (sample): {str(parsed_data)[:1000]}")
                print("====================================\n")
            
            results = []
            
            # Process each item in the parsed data
            if isinstance(parsed_data, list):
                for item in parsed_data:
                    if isinstance(item, dict) and "question_id" in item and "incorrect_answers" in item:
                        question_id = item["question_id"]
                        incorrect_answers = item["incorrect_answers"]
                        
                        # Validate question ID
                        if question_id in question_map:
                            # Clean and validate incorrect answers
                            if isinstance(incorrect_answers, list) and all(isinstance(a, str) for a in incorrect_answers):
                                # Clean each answer
                                cleaned_answers = [clean_text(a) for a in incorrect_answers if a]
                                
                                # Filter out any answers that match the correct answer
                                correct_answer = question_map[question_id].answer.lower()
                                filtered_answers = [a for a in cleaned_answers if a.lower() != correct_answer]
                                
                                if filtered_answers:
                                    results.append((question_id, filtered_answers))
                                else:
                                    logger.warning(f"All generated incorrect answers matched the correct answer for question {question_id}")
                            else:
                                logger.warning(f"Invalid incorrect_answers format for question {question_id}")
                        else:
                            logger.warning(f"Unknown question_id in response: {question_id}")
            
            # If we couldn't parse anything useful, generate some dummy incorrect answers
            if not results:
                logger.warning("Could not parse any valid incorrect answers from LLM response")
                
                # Generate fallback incorrect answers based on question type
                fallback_results = []
                for q in questions:
                    # Create generic fallback incorrect answers
                    fallback_answers = self._generate_fallback_incorrect_answers(q.answer)
                    fallback_results.append((q.id, fallback_answers))
                
                return fallback_results
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing incorrect answers response: {str(e)}")
            if self.debug_enabled:
                print(f"Error parsing incorrect answers: {str(e)}")
            
            # Return empty results on parsing error
            return [(q.id, []) for q in questions]
    
    def _generate_fallback_incorrect_answers(self, correct_answer: str) -> List[str]:
        """
        Generate fallback incorrect answers when parsing fails.
        
        Args:
            correct_answer: The correct answer to avoid duplicating
            
        Returns:
            List of generic incorrect answers
        """
        # Simple fallback strategy - generic incorrect answers
        # This is not ideal but prevents complete failure
        return [
            f"Not {correct_answer}",
            f"Alternative to {correct_answer}",
            f"Option C"
        ]