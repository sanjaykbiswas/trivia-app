# backend/src/utils/question_generation/question_generator.py
"""
Utility for generating trivia questions using LLM based on pack topics and difficulty.
"""

import json
from typing import List, Dict, Any, Optional, Union
import logging
import traceback
# Assuming DifficultyLevel is correctly imported from your models
from ...models.question import DifficultyLevel, Question
from ..llm.llm_service import LLMService
# Assuming parse_json_from_llm is correctly imported
from ..llm.llm_parsing_utils import parse_json_from_llm
# Assuming clean_text is correctly imported
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
            difficulty_descriptions: Dictionary with difficulty descriptions for ALL levels
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
            difficulty=difficulty_str, # Pass the TARGET difficulty
            difficulty_descriptions=difficulty_descriptions, # Pass ALL descriptions
            seed_questions=seed_questions,
            custom_instructions=custom_instructions,
            num_questions=num_questions
        )

        if self.debug_enabled:
            print("\n=== Question Generation Prompt ===")
            print(prompt)
            print("==================================\n")

        try:
            # Generate questions using LLM
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
                difficulty_str=difficulty_str # Pass the target difficulty
            )

            self.last_processed_questions = processed_questions

            if self.debug_enabled:
                print("\n=== Processed Questions ===")
                # Use safe JSON serialization for debug output
                try:
                    # Use model_dump for Pydantic V2 if applicable, otherwise default=str
                    print(json.dumps(processed_questions, indent=2, default=str))
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

    # --- NEW HELPER METHOD ---
    def _format_all_difficulty_descriptions(
        self,
        difficulty_descriptions: Dict[str, Dict[str, str]]
    ) -> str:
        """Formats all difficulty descriptions for inclusion in the LLM prompt."""
        formatted_lines = []
        # Ensure consistent order
        levels = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        for level in levels:
            if level in difficulty_descriptions:
                descriptions = difficulty_descriptions[level]
                base_desc = descriptions.get("base", "").strip()
                custom_desc = descriptions.get("custom", "").strip()
                # Combine descriptions, avoiding double periods if one is empty
                combined_desc = base_desc
                if custom_desc:
                    if combined_desc and not combined_desc.endswith('.'):
                        combined_desc += ". "
                    elif not combined_desc:
                         pass # Use custom directly
                    combined_desc += custom_desc
                # Ensure it ends with a period if there's content
                if combined_desc and not combined_desc.endswith('.'):
                     combined_desc += '.'

                if combined_desc: # Only add if there's a description
                    formatted_lines.append(f"*   {level}: {combined_desc}")

        if not formatted_lines:
            return "No specific difficulty descriptions were generated for this pack."

        return "\n".join(formatted_lines)
    # --- END NEW HELPER METHOD ---

    # --- UPDATED METHOD ---
    def _build_question_generation_prompt(
        self,
        creation_name: str,
        pack_topic: str,
        difficulty: str, # The TARGET difficulty (e.g., "Medium")
        difficulty_descriptions: Dict[str, Dict[str, str]], # ALL descriptions
        seed_questions: Dict[str, str] = None,
        custom_instructions: Optional[str] = None,
        num_questions: int = 5
    ) -> str:
        """
        Build the prompt for question generation, including ALL difficulty descriptions for context.
        """
        # Format ALL difficulty descriptions
        all_descriptions_text = self._format_all_difficulty_descriptions(difficulty_descriptions)

        # Format seed questions (no change needed here)
        examples_text = self._format_seed_questions_as_examples(seed_questions)

        # Build the prompt - MODIFIED to include all descriptions and target difficulty
        prompt = f"""Generate {num_questions} trivia questions about "{pack_topic}" for a trivia pack called "{creation_name}".

The TARGET difficulty level for these questions is: {difficulty}.

Use the following descriptions for ALL difficulty levels in this pack as context to understand what {difficulty} means relative to the others:
{all_descriptions_text}

Each generated question should:
1. Be clear and unambiguous.
2. Have a single correct answer that is factually accurate. The question should also have factually correct elements.
3. Not state the answer within the question text itself. E.g., "Question: Who is the main character of Harry Potter" is a bad question because the answer is "Harry Potter."
4. Be specific to the topic "{pack_topic}".
5. Match the TARGET difficulty level ({difficulty}) based on the provided context.
""" # <-- Add any other constraints you had here (6, 7, etc.)

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
- Generate questions ONLY for the TARGET difficulty level: {difficulty}.
- Make sure each question has exactly ONE correct answer.
- Return ONLY the JSON array without any additional text or markdown formatting.
- Ensure the JSON is properly formatted.
- Ensure the question length is appropriate (e.g., 10-20 words or max 125 characters).
- Make the questions interesting and creative while maintaining accuracy.
- Ensure answers are concise.
"""
        return prompt
    # --- END UPDATED METHOD ---

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

        # Limit to 5 examples to keep prompt concise
        for question, answer in seed_questions.items():
            examples.append(f"Question: {question}\nAnswer: {answer}")
            count += 1
            if count >= 5:
                break

        if examples:
            return f"""
Here are some example questions and answers for this pack and topic:

{"\n\n".join(examples)}

Use the instructions and example questions as inspiration, but create entirely new questions that play with wordplay, allusions, and clever phrasing that ties to the topic without being too on-the-nose.
Ensure you follow all instructions listed. Above all, the question and answer created must be correct. Do not let style or creativity override accuracy.
"""
        return ""

    async def _process_question_response(
        self,
        response: str,
        pack_id: str,
        pack_topic: str,
        difficulty_str: str # Target difficulty string
    ) -> List[Dict[str, Any]]:
        """
        Process the LLM response into structured question data.

        Args:
            response: Raw response from LLM
            pack_id: ID of the pack
            pack_topic: Topic the questions are about
            difficulty_str: Target difficulty level string

        Returns:
            List of dictionaries containing structured question data
        """
        # Map the TARGET difficulty string to DifficultyLevel enum
        try:
            target_difficulty = DifficultyLevel(difficulty_str.lower())
        except ValueError:
            logger.warning(f"Invalid target difficulty level '{difficulty_str}', defaulting to MEDIUM")
            target_difficulty = DifficultyLevel.MEDIUM

        # Parse the JSON response
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

                    # Basic validation (e.g., non-empty)
                    if not question_text or not answer_text:
                        logger.warning(f"Skipping question with empty content/answer: {item}")
                        continue

                    # Create a structured question dict
                    # Assign the TARGET difficulty as both initial and current
                    question_dict = {
                        "question": question_text,
                        "answer": answer_text,
                        "pack_id": pack_id,  # Assumes pack_id is already a string
                        "pack_topics_item": pack_topic,
                        "difficulty_initial": target_difficulty, # Use the target enum
                        "difficulty_current": target_difficulty  # Use the target enum
                    }

                    structured_questions.append(question_dict)

                    if self.debug_enabled:
                        # Use model_dump if the dict contains Pydantic models/enums
                        print(f"Structured question: {json.dumps(question_dict, default=lambda x: x.value if isinstance(x, DifficultyLevel) else str(x))}")
                else:
                    logger.warning(f"Skipping invalid question format in LLM response: {item}")
        else:
            logger.error(f"Failed to parse questions response as a list: {type(questions_data)}")
            if self.debug_enabled:
                print(f"Failed to parse questions response as a list. Type: {type(questions_data)}")

        return structured_questions