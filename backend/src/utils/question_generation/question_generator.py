# backend/src/utils/question_generation/question_generator.py
"""
Utility for generating trivia questions using LLM based on pack topics and difficulty.
"""

import json
from typing import List, Dict, Any, Optional, Union
import logging
import traceback
from ...models.question import DifficultyLevel, Question
from ..llm.llm_service import LLMService
from ..llm.llm_parsing_utils import parse_json_from_llm
from ..document_processing.processors import clean_text

# Configure logger
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Generates trivia questions using LLM based on specified topics and difficulties.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the question generator with services.
        
        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()
        self.debug_enabled = False
        self.last_raw_response = None
        self.last_processed_questions = None
    
    async def generate_questions(
        self, 
        pack_id: str,
        creation_name: str,
        pack_topic: str,
        difficulty: Union[str, DifficultyLevel],
        difficulty_descriptions: Dict[str, Dict[str, str]],
        seed_questions: Dict[str, str] = None,
        custom_instructions: Optional[str] = None,
        num_questions: int = 5,
        debug_mode: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate questions for a specific topic and difficulty.
        
        Args:
            pack_id: ID of the pack
            creation_name: Name of the trivia pack
            pack_topic: The specific topic to generate questions for
            difficulty: Difficulty level for the questions
            difficulty_descriptions: Dictionary with difficulty descriptions
            seed_questions: Optional dictionary of example questions and answers
            custom_instructions: Optional custom instructions for question generation
            num_questions: Number of questions to generate
            debug_mode: Enable verbose debug output
            
        Returns:
            List of dictionaries containing question data ready to be stored
        """
        self.debug_enabled = debug_mode
        
        # Ensure we have valid difficulty level string
        if isinstance(difficulty, DifficultyLevel):
            difficulty_str = difficulty.value.capitalize()
        else:
            difficulty_str = difficulty.capitalize()
        
        # Build prompt for question generation
        prompt = self._build_question_generation_prompt(
            creation_name=creation_name,
            pack_topic=pack_topic,
            difficulty=difficulty_str,
            difficulty_descriptions=difficulty_descriptions,
            seed_questions=seed_questions,
            custom_instructions=custom_instructions,
            num_questions=num_questions
        )
        
        if self.debug_enabled:
            print("\n=== Question Generation Prompt ===")
            print(prompt)
            print("==================================\n")
        
        try:
            # Generate questions using LLM (CHANGED: removed await)
            raw_response = self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.7,  # Slightly higher temperature for creativity
                max_tokens=2000   # Ensure enough tokens for multiple questions
            )
            
            self.last_raw_response = raw_response
            
            if self.debug_enabled:
                print("\n=== Raw LLM Response ===")
                print(raw_response)
                print("========================\n")
            
            # Process the response
            processed_questions = await self._process_question_response(
                response=raw_response,
                pack_id=pack_id,
                pack_topic=pack_topic,
                difficulty_str=difficulty_str
            )
            
            self.last_processed_questions = processed_questions
            
            if self.debug_enabled:
                print("\n=== Processed Questions ===")
                # Use safe JSON serialization for debug output
                try:
                    print(json.dumps(processed_questions, indent=2))
                except Exception as e:
                    print(f"Error showing processed questions: {str(e)}")
                    print(f"Raw processed questions: {processed_questions}")
                print("===========================\n")
            
            return processed_questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            if self.debug_enabled:
                print(f"\n=== Question Generation Error ===")
                print(f"Error: {str(e)}")
                print(traceback.format_exc())
                print("================================\n")
            return []
    
    def _build_question_generation_prompt(
        self,
        creation_name: str,
        pack_topic: str,
        difficulty: str,
        difficulty_descriptions: Dict[str, Dict[str, str]],
        seed_questions: Dict[str, str] = None,
        custom_instructions: Optional[str] = None,
        num_questions: int = 5
    ) -> str:
        """
        Build the prompt for question generation.
        
        Args:
            creation_name: Name of the trivia pack
            pack_topic: Topic to generate questions about
            difficulty: Difficulty level string
            difficulty_descriptions: Dictionary with difficulty descriptions
            seed_questions: Optional dictionary of example questions and answers
            custom_instructions: Optional custom instructions for LLM question generation
            num_questions: Number of questions to generate
            
        Returns:
            Formatted prompt string
        """
        # Get the relevant difficulty description
        diff_description = ""
        if difficulty in difficulty_descriptions:
            base_desc = difficulty_descriptions[difficulty].get("base", "")
            custom_desc = difficulty_descriptions[difficulty].get("custom", "")
            diff_description = f"{base_desc} {custom_desc}".strip()
        else:
            # Fallback if the specific difficulty isn't found
            diff_description = f"{difficulty} difficulty questions about the topic."
        
        # Format seed questions as examples if provided
        examples_text = self._format_seed_questions_as_examples(seed_questions)
        
        # Build the prompt
        prompt = f"""Generate {num_questions} trivia questions about {pack_topic} for a trivia pack called "{creation_name}".

The questions should be at {difficulty} difficulty level.
Difficulty description: {diff_description}

Each question should:
1. Be clear and unambiguous
2. Have a single correct answer that is factually accurate
3. Be specific to the topic of {pack_topic}
4. Be at the appropriate {difficulty} difficulty level
"""

        # Add custom instructions if provided
        if custom_instructions:
            prompt += f"\nAdditional instructions for question generation:\n{custom_instructions}\n"

        # Add examples and format instructions
        prompt += f"""
{examples_text}

Return ONLY a valid JSON array of question objects with the following format:
[
  {{
    "question": "The full question text?",
    "answer": "The correct answer"
  }},
  ...
]

IMPORTANT: 
- Make sure each question has exactly ONE correct answer
- Return ONLY the JSON array without any additional text
- Ensure the JSON is properly formatted
- Each question should be appropriate for the {difficulty} difficulty level
- Make the questions interesting and creative while maintaining accuracy
"""
        return prompt
    
    def _format_seed_questions_as_examples(self, seed_questions: Optional[Dict[str, str]]) -> str:
        """
        Format seed questions as examples for the prompt.
        
        Args:
            seed_questions: Dictionary mapping questions to answers
            
        Returns:
            Formatted examples string
        """
        if not seed_questions:
            return ""
        
        examples = []
        count = 0
        
        # Limit to 3 examples to keep prompt concise
        for question, answer in seed_questions.items():
            examples.append(f"Question: {question}\nAnswer: {answer}")
            count += 1
            if count >= 3:
                break
        
        if examples:
            return f"""
Here are some example questions and answers for this pack:

{"\n\n".join(examples)}

Please use these as a guide for style and format, but create completely new questions.
"""
        return ""
    
    async def _process_question_response(  # Kept as async because it calls parse_json_from_llm
        self,
        response: str,
        pack_id: str,
        pack_topic: str,
        difficulty_str: str
    ) -> List[Dict[str, Any]]:
        """
        Process the LLM response into structured question data.
        
        Args:
            response: Raw response from LLM
            pack_id: ID of the pack
            pack_topic: Topic the questions are about
            difficulty_str: Difficulty level string
            
        Returns:
            List of dictionaries containing structured question data
        """
        # Map the difficulty string to DifficultyLevel enum
        try:
            difficulty = DifficultyLevel(difficulty_str.lower())
        except ValueError:
            # Default to MEDIUM if the difficulty doesn't match any enum value
            logger.warning(f"Invalid difficulty level '{difficulty_str}', defaulting to MEDIUM")
            difficulty = DifficultyLevel.MEDIUM
        
        # Parse the JSON response (KEPT: await since parse_json_from_llm is async)
        questions_data = await parse_json_from_llm(response, [])
        
        if self.debug_enabled:
            print("\n=== Parsed JSON from LLM ===")
            print(f"Type: {type(questions_data)}")
            print(f"Content: {questions_data}")
            print("============================\n")
        
        structured_questions = []
        
        # Validate and structure each question
        if isinstance(questions_data, list):
            for item in questions_data:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    # Clean the question and answer text
                    question_text = clean_text(item["question"])
                    answer_text = clean_text(item["answer"])
                    
                    # Create a structured question dict
                    question_dict = {
                        "question": question_text,
                        "answer": answer_text,
                        "pack_id": pack_id,  # Already a string ID
                        "pack_topics_item": pack_topic,
                        "difficulty_initial": difficulty,
                        "difficulty_current": difficulty
                    }
                    
                    structured_questions.append(question_dict)
                    
                    if self.debug_enabled:
                        print(f"Structured question: {question_dict}")
                else:
                    logger.warning(f"Skipping invalid question format: {item}")
        else:
            logger.error(f"Failed to parse questions response as a list: {type(questions_data)}")
            if self.debug_enabled:
                print(f"Failed to parse questions response as a list. Type: {type(questions_data)}")
        
        return structured_questions