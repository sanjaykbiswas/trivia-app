# backend/src/utils/question_generation/question_validator.py
"""
Utility for validating and correcting trivia questions before storage.
This module acts as a quality control layer between question generation and storage.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text
from ..llm.llm_parsing_utils import parse_json_from_llm

# Configure logger
logger = logging.getLogger(__name__)

class QuestionValidator:
    """
    Validates generated trivia questions for accuracy and quality.
    
    This validator performs the following checks:
    - Verifies factual accuracy of answers
    - Removes questions where the answer appears in the question
    - Fixes JSON structural issues
    - Removes truncated or incomplete questions
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the question validator with services.
        
        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()
        self.debug_enabled = False
        
    async def validate_and_correct_questions(
        self, 
        questions: List[Dict[str, Any]],
        debug_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Validate and correct a batch of questions.
        
        Args:
            questions: List of question objects to validate
            debug_mode: Whether to output debug information
            
        Returns:
            Filtered list of corrected questions
        """
        self.debug_enabled = debug_mode
        
        if not questions:
            return []
            
        if self.debug_enabled:
            print(f"\n=== Starting Question Validation ===")
            print(f"Number of questions before validation: {len(questions)}")
        
        # Step 1: Remove questions where the answer appears in the question
        filtered_questions = self._filter_answer_in_question(questions)
        
        if self.debug_enabled:
            removed = len(questions) - len(filtered_questions)
            print(f"Removed {removed} questions where answer appears in question")
        
        # Step 2: Remove structurally invalid questions
        valid_questions = self._filter_invalid_questions(filtered_questions)
        
        if self.debug_enabled:
            removed = len(filtered_questions) - len(valid_questions)
            print(f"Removed {removed} structurally invalid questions")
        
        # Process questions in batches of maximum 50
        batch_size = 50
        batches = [valid_questions[i:i + batch_size] for i in range(0, len(valid_questions), batch_size)]
        
        corrected_questions = []
        for i, batch in enumerate(batches):
            if self.debug_enabled:
                print(f"Processing batch {i+1}/{len(batches)} ({len(batch)} questions)")
            
            # Step 3: Verify and correct answers with LLM
            corrected_batch = await self._verify_and_correct_answers(batch)
            corrected_questions.extend(corrected_batch)
        
        if self.debug_enabled:
            print(f"Number of questions after validation: {len(corrected_questions)}")
            print(f"=== Question Validation Complete ===\n")
        
        return corrected_questions
    
    def _filter_answer_in_question(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out questions where the answer appears in the question.
        
        Args:
            questions: List of question objects
            
        Returns:
            Filtered list of questions
        """
        filtered = []
        
        for question in questions:
            if not self._answer_appears_in_question(question.get("question", ""), question.get("answer", "")):
                filtered.append(question)
            elif self.debug_enabled:
                print(f"Removed question: '{question.get('question', '')}' - Answer '{question.get('answer', '')}' appears in question.")
                
        return filtered
    
    def _answer_appears_in_question(self, question: str, answer: str) -> bool:
        """
        Check if the answer appears in the question.
        
        Args:
            question: The question text
            answer: The answer text
            
        Returns:
            True if the answer appears in the question, False otherwise
        """
        if not question or not answer:
            return False
            
        # Clean and normalize both texts for comparison
        clean_question = clean_text(question.lower())
        clean_answer = clean_text(answer.lower())
        
        # Check for exact match
        if clean_answer in clean_question:
            return True
            
        # Check for almost exact match (allowing for minor differences)
        answer_words = clean_answer.split()
        
        # For very short answers (1-2 words), check more strictly
        if len(answer_words) <= 2:
            return clean_answer in clean_question
            
        # For longer answers, check if most of the answer is in the question
        threshold = 0.8  # 80% of words need to match
        words_present = sum(1 for word in answer_words if word in clean_question.split())
        ratio = words_present / len(answer_words)
        
        return ratio >= threshold
    
    def _filter_invalid_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out structurally invalid or truncated questions.
        
        Args:
            questions: List of question objects
            
        Returns:
            Filtered list of valid questions
        """
        valid = []
        
        for question in questions:
            # Check for required fields
            if not isinstance(question, dict):
                continue
                
            if "question" not in question or "answer" not in question:
                continue
                
            # Check for non-empty values
            if not question["question"].strip() or not question["answer"].strip():
                continue
                
            # Check for truncated question texts (ending with ellipsis or incomplete sentences)
            q_text = question["question"].strip()
            if q_text.endswith("...") or q_text.endswith("…"):
                continue
                
            # Check for common completion cutoff patterns
            if re.search(r'\b(therefore|thus|hence|so|in conclusion)\b\s*$', q_text, re.IGNORECASE):
                continue
                
            valid.append(question)
            
        return valid
    
    async def _verify_and_correct_answers(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify answers using LLM and correct if necessary.
        
        Args:
            questions: Batch of questions to verify
            
        Returns:
            List of questions with corrected answers
        """
        if not questions:
            return []
            
        # Create prompt for verification
        prompt = self._build_verification_prompt(questions)
        
        try:
            # Use LLM to verify and correct answers
            raw_response = self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for factual accuracy
                max_tokens=2000
            )
            
            if self.debug_enabled:
                print("\n=== LLM Verification Response ===")
                print(raw_response[:500] + "..." if len(raw_response) > 500 else raw_response)
                print("================================\n")
            
            # Parse the LLM response
            corrections = await parse_json_from_llm(raw_response, [])
            
            # Apply corrections
            return self._apply_corrections(questions, corrections)
            
        except Exception as e:
            logger.error(f"Error verifying questions: {str(e)}")
            if self.debug_enabled:
                print(f"Error verifying questions: {str(e)}")
            
            # Return original questions if verification fails
            return questions
    
    def _build_verification_prompt(self, questions: List[Dict[str, Any]]) -> str:
        """
        Build prompt for verifying and correcting answers.
        
        Args:
            questions: List of questions to verify
            
        Returns:
            Formatted prompt string
        """
        # Convert questions to JSON for the prompt
        questions_json = json.dumps([
            {"id": idx, "question": q.get("question", ""), "answer": q.get("answer", "")}
            for idx, q in enumerate(questions)
        ], indent=2)
        
        prompt = f"""Verify the correctness of the following trivia questions and answers. For each question:
1. Check if the answer is factually correct
2. If the answer is incorrect, provide the correct answer

Return your analysis as a JSON array where each object contains:
- id: The original question ID
- needs_correction: true/false indicating if the answer needs correction
- corrected_answer: The correct answer (only if needs_correction is true)
- reason: A brief explanation for the correction (only if needs_correction is true)

Here are the questions to verify:
{questions_json}

IMPORTANT:
- Only correct answers that are factually wrong
- Do not change correct answers that are merely phrased differently
- Be certain of your corrections - only mark an answer as needing correction if you're confident the original is wrong
- Return ONLY the JSON array without any additional text
- Keep your reasoning concise and focused on factual accuracy

Example output format:
[
  {{
    "id": 0,
    "needs_correction": true,
    "corrected_answer": "Albert Einstein",
    "reason": "The original answer 'Isaac Newton' is incorrect. Einstein developed the theory of relativity."
  }},
  {{
    "id": 1,
    "needs_correction": false
  }}
]
"""
        return prompt
    
    def _apply_corrections(
        self, 
        original_questions: List[Dict[str, Any]], 
        corrections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply corrections to original questions.
        
        Args:
            original_questions: List of original question objects
            corrections: List of correction objects from LLM
            
        Returns:
            List of corrected question objects
        """
        # If no corrections returned or parsing failed, return originals
        if not isinstance(corrections, list):
            return original_questions
            
        corrected_questions = []
        
        for i, question in enumerate(original_questions):
            corrected = question.copy()
            
            # Find the correction for this question
            for correction in corrections:
                if not isinstance(correction, dict):
                    continue
                    
                if correction.get("id") == i and correction.get("needs_correction") is True:
                    new_answer = correction.get("corrected_answer")
                    
                    if new_answer and isinstance(new_answer, str) and new_answer.strip():
                        corrected["answer"] = new_answer.strip()
                        
                        if self.debug_enabled:
                            print(f"Corrected answer for '{question.get('question', '')[:30]}...'")
                            print(f"  Original: '{question.get('answer', '')}'")
                            print(f"  Corrected: '{new_answer}'")
                            print(f"  Reason: {correction.get('reason', 'No reason provided')}")
                    
                    break
            
            corrected_questions.append(corrected)
            
        return corrected_questions