# backend/src/utils/question_generation/seed_question_processor.py
"""
Utility for processing seed questions from various input formats (CSV, text)
and converting them to standardized JSON output for storage in Supabase.
"""

import json
import csv
import io
import re
from typing import Dict, List, Union, Optional
import uuid
import logging
from ...utils.llm.llm_service import LLMService
from ...utils.document_processing.processors import clean_text
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ...models.pack_creation_data import PackCreationDataUpdate
from ...utils import ensure_uuid
from ...utils.llm.llm_parsing_utils import parse_json_from_llm

# Configure logger
logger = logging.getLogger(__name__)

class SeedQuestionProcessor:
    """
    Processes seed questions from various input formats and
    converts them to standardized JSON for storage.
    """
    
    def __init__(self, pack_creation_repository: Optional[PackCreationDataRepository] = None, 
                 llm_service: Optional[LLMService] = None):
        """
        Initialize with optional repositories and services.
        
        Args:
            pack_creation_repository: Repository for pack creation data operations
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.pack_creation_repository = pack_creation_repository
        self.llm_service = llm_service or LLMService()
    
    async def process_csv_content(self, csv_content: str, 
                                  question_column: str = "question", 
                                  answer_column: str = "answer") -> Dict[str, str]:
        """
        Process CSV content to extract question-answer pairs.
        
        Args:
            csv_content: Raw CSV content as string
            question_column: Name of the column containing questions
            answer_column: Name of the column containing answers
            
        Returns:
            Dictionary of question-answer pairs
        """
        result = {}
        
        try:
            # Use CSV reader to parse the content
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            
            # Check if the required columns exist
            fieldnames = reader.fieldnames or []
            lowercase_fieldnames = [field.lower() for field in fieldnames]
            
            # Find the matching columns (case-insensitive)
            question_idx = None
            answer_idx = None
            
            for i, field in enumerate(lowercase_fieldnames):
                if field == question_column.lower():
                    question_idx = i
                elif field == answer_column.lower():
                    answer_idx = i
            
            # If column names don't match exactly, try to find by substring
            if question_idx is None:
                for i, field in enumerate(lowercase_fieldnames):
                    if "question" in field.lower():
                        question_idx = i
                        break
            
            if answer_idx is None:
                for i, field in enumerate(lowercase_fieldnames):
                    if "answer" in field.lower():
                        answer_idx = i
                        break
            
            # If still not found, use the first two columns
            if question_idx is None and len(fieldnames) > 0:
                question_idx = 0
            
            if answer_idx is None and len(fieldnames) > 1:
                answer_idx = 1
            
            # If we have the necessary columns, extract the Q&A pairs
            if question_idx is not None and answer_idx is not None:
                # Restart the reader from the beginning
                csv_file.seek(0)
                reader = csv.DictReader(csv_file)
                
                # Get the actual column names
                q_col = fieldnames[question_idx]
                a_col = fieldnames[answer_idx]
                
                for row in reader:
                    question = clean_text(row[q_col])
                    answer = clean_text(row[a_col])
                    
                    if question and answer:  # Only add non-empty pairs
                        result[question] = answer
            else:
                logger.warning(f"Required columns not found in CSV. Available columns: {fieldnames}")
        
        except Exception as e:
            logger.error(f"Error processing CSV content: {str(e)}")
            # Re-raise for proper error handling upstream
            raise
        
        return result
    
    async def process_text_content(self, text_content: str) -> Dict[str, str]:
        """
        Process raw text content using LLM to extract question-answer pairs.
        
        Args:
            text_content: Raw text containing questions and answers
            
        Returns:
            Dictionary of question-answer pairs
        """
        # Clean the text
        cleaned_text = clean_text(text_content)
        
        # Create prompt for LLM
        prompt = self._build_extraction_prompt(cleaned_text)
        
        # Generate JSON using LLM
        raw_response = await self.llm_service.generate_content(prompt)
        processed_response = await self.llm_service.process_llm_response(raw_response)
        
        # Parse the JSON response
        result = self._parse_json_response(processed_response)
        
        return result
    
    def _build_extraction_prompt(self, text_content: str) -> str:
        """
        Build the prompt for LLM to extract question-answer pairs.
        
        Args:
            text_content: Cleaned text content
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Extract all question-answer pairs from the following text content. 
Return ONLY a valid JSON object where the keys are questions and the values are answers.

Text content:
{text_content}

Format the output as a valid JSON object with this structure:
{{
  "Question 1": "Answer 1",
  "Question 2": "Answer 2",
  "Question 3": "Answer 3"
}}

IMPORTANT: 
1. Extract ONLY clear question-answer pairs. Do not invent questions or answers.
2. Return ONLY the JSON object without any additional text or explanations.
3. Make sure the JSON is valid with proper escaping of special characters.
4. Do not include any text outside the JSON structure.
"""
        return prompt
    
    def _parse_json_response(self, response: str) -> Dict[str, str]:
        """
        Parse the JSON response from LLM.
        
        Args:
            response: JSON response from LLM
            
        Returns:
            Dictionary of question-answer pairs
        """
        try:
            # Use the existing LLM parsing utility from the codebase
            result = parse_json_from_llm(response, {})
            
            # Ensure all keys and values are strings
            if isinstance(result, dict):
                return {str(k): str(v) for k, v in result.items()}
            else:
                logger.warning("Failed to extract valid JSON object from LLM response")
                
                # Fall back to regex-based extraction if needed
                qa_pattern = r'"([^"]+)"\s*:\s*"([^"]+)"'
                matches = re.findall(qa_pattern, response)
                
                if matches:
                    return {match[0]: match[1] for match in matches}
                return {}
                
        except Exception as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            return {}
    
    async def detect_and_process_input(self, input_content: str) -> Dict[str, str]:
        """
        Detect input type and process accordingly.
        
        Args:
            input_content: Raw input content (CSV or text)
            
        Returns:
            Dictionary of question-answer pairs
        """
        # Simple heuristic: if it contains commas and newlines, it's likely a CSV
        is_likely_csv = ',' in input_content and '\n' in input_content
        
        # Try to parse as CSV first if it looks like one
        if is_likely_csv:
            try:
                # Check if it has a header row with potential column names
                first_line = input_content.strip().split('\n')[0]
                if 'question' in first_line.lower() or 'answer' in first_line.lower():
                    result = await self.process_csv_content(input_content)
                    
                    # If we got results, return them
                    if result:
                        return result
                    
                    # If not, fall back to LLM processing
                    logger.warning("CSV detection failed to extract valid Q&A pairs, falling back to LLM processing")
            except Exception as e:
                logger.warning(f"CSV processing failed: {str(e)}, falling back to LLM processing")
        
        # If not CSV or CSV processing failed, use LLM to extract Q&A pairs
        return await self.process_text_content(input_content)
    
    async def store_seed_questions(self, pack_id: uuid.UUID, seed_questions: Dict[str, str]) -> bool:
        """
        Store seed questions in the pack_creation_data table.
        
        Args:
            pack_id: UUID of the pack
            seed_questions: Dictionary of question-answer pairs
            
        Returns:
            Success flag
        """
        if not self.pack_creation_repository:
            logger.error("Pack creation repository not provided. Cannot store seed questions.")
            return False
        
        try:
            # Ensure pack_id is a proper UUID object
            pack_id = ensure_uuid(pack_id)
            
            # Check if there's already data for this pack
            existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
            
            if existing_data:
                # Update existing record
                update_data = PackCreationDataUpdate(
                    seed_questions=seed_questions
                )
                await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
                return True
            else:
                logger.warning(f"No existing pack creation data found for pack_id {pack_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing seed questions: {str(e)}")
            return False