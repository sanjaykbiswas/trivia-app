# backend/src/utils/question_generation/question_generator.py
"""
Utility for generating trivia questions using LLM based on pack topics and difficulty.
"""

import json
from typing import List, Dict, Any, Optional, Union
import logging
import traceback

# --- UPDATED IMPORTS ---
from ...models.question import DifficultyLevel, Question # Keep Question import for type hint if needed elsewhere, though not directly used here
from ..llm.llm_service import LLMService
from ..llm.llm_parsing_utils import parse_json_from_llm
from ..document_processing.processors import clean_text
# --- END UPDATED IMPORTS ---

# Configure logger
logger = logging.getLogger(__name__)

# --- Example format moved outside f-string ---
QUESTION_JSON_EXAMPLE_FORMAT = """
[
  {
    "question": "The full question text?",
    "answer": "The correct answer"
  },
  {
    "question": "Another question?",
    "answer": "Its answer"
  }
]
"""
# --- End Example format ---


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

    # --- UPDATED METHOD SIGNATURE ---
    async def generate_questions(
        self,
        pack_id: str,
        pack_name: str, # <<< CHANGED: Use pack_name instead of creation_name
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
            pack_id: ID of the pack.
            pack_name: Name of the trivia pack (used instead of creation_name).
            pack_topic: The specific topic to generate questions for.
            difficulty: Difficulty level for the questions.
            difficulty_descriptions: Dictionary with difficulty descriptions for ALL levels.
            seed_questions: Optional dictionary of example questions and answers.
            custom_instructions: Optional custom instructions for question generation.
            num_questions: Number of questions to generate.
            debug_mode: Enable verbose debug output.

        Returns:
            List of dictionaries containing question data ready to be stored.
        """
        # --- END UPDATED SIGNATURE ---
        self.debug_enabled = debug_mode

        # Ensure we have valid difficulty level string
        if isinstance(difficulty, DifficultyLevel):
            difficulty_str = difficulty.value.capitalize()
        else:
            difficulty_str = difficulty.capitalize()

        # Build prompt for question generation (using pack_name)
        prompt = self._build_question_generation_prompt(
            pack_name=pack_name, # <<< CHANGED: Pass pack_name
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
            # Generate questions using LLM
            raw_response = self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000
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
                try:
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

    def _format_all_difficulty_descriptions(
        self,
        difficulty_descriptions: Dict[str, Dict[str, str]]
    ) -> str:
        """Formats all difficulty descriptions for inclusion in the LLM prompt."""
        formatted_lines = []
        levels = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        for level in levels:
            if level in difficulty_descriptions:
                descriptions = difficulty_descriptions[level]
                base_desc = descriptions.get("base", "").strip()
                custom_desc = descriptions.get("custom", "").strip()
                combined_desc = base_desc
                if custom_desc:
                    if combined_desc and not combined_desc.endswith('.'):
                        combined_desc += ". "
                    elif not combined_desc:
                         pass
                    combined_desc += custom_desc
                if combined_desc and not combined_desc.endswith('.'):
                     combined_desc += '.'
                if combined_desc:
                    formatted_lines.append(f"*   {level}: {combined_desc}")
        if not formatted_lines:
            return "No specific difficulty descriptions were generated for this pack."
        return "\n".join(formatted_lines)

    # --- UPDATED METHOD SIGNATURE ---
    def _build_question_generation_prompt(
        self,
        pack_name: str, # <<< Ensure this uses pack_name
        pack_topic: str,
        difficulty: str,
        difficulty_descriptions: Dict[str, Dict[str, str]],
        seed_questions: Dict[str, str] = None,
        custom_instructions: Optional[str] = None,
        num_questions: int = 5
    ) -> str:
        """Build the prompt for question generation using string concatenation."""
        all_descriptions_text = self._format_all_difficulty_descriptions(difficulty_descriptions)
        examples_text = self._format_seed_questions_as_examples(seed_questions)
        # Pre-format the optional instruction text
        instruction_text = f"\nAdditional instructions for question generation:\n{custom_instructions}\n" if custom_instructions else ""

        # --- Build the prompt using concatenation ---
        prompt = f"Generate {num_questions} trivia questions about \"{pack_topic}\" for a trivia pack called \"{pack_name}\".\n\n"
        prompt += f"The TARGET difficulty level for these questions is: {difficulty}.\n\n"
        prompt += "Use the following descriptions for ALL difficulty levels in this pack as context to understand what {difficulty} means relative to the others:\n"
        prompt += f"{all_descriptions_text}\n\n" # Add the formatted descriptions
        prompt += "Each generated question should:\n"
        prompt += "1. Be clear and unambiguous.\n"
        prompt += "2. Have a single correct answer that is factually accurate. The question should also have factually correct elements.\n"
        prompt += "3. Not state the answer within the question text itself. E.g., \"Question: Who is the main character of Harry Potter\" is a bad question because the answer is \"Harry Potter.\"\n"
        prompt += f"4. Be specific to the topic \"{pack_topic}\".\n"
        prompt += f"5. Match the TARGET difficulty level ({difficulty}) based on the provided context.\n"
        prompt += "6. Be interesting and creative while maintaining accuracy.\n"
        prompt += "7. Have a question length appropriate for trivia (e.g., 10-20 words or max 125 characters).\n"
        prompt += "8. Have a concise answer.\n"
        prompt += instruction_text # Add optional instructions
        prompt += examples_text # Add optional examples
        prompt += "\nReturn ONLY a valid JSON array of question objects with the following format:\n"
        prompt += QUESTION_JSON_EXAMPLE_FORMAT # Add the pre-defined example format
        prompt += "\nIMPORTANT:\n"
        prompt += f"- Generate questions ONLY for the TARGET difficulty level: {difficulty}.\n"
        prompt += "- Make sure each question has exactly ONE correct answer.\n"
        prompt += "- Return ONLY the JSON array without any additional text or markdown formatting.\n"
        prompt += "- Ensure the JSON is properly formatted.\n"
        # --- End prompt building ---

        return prompt

    def _format_seed_questions_as_examples(self, seed_questions: Optional[Dict[str, str]]) -> str:
        """Format seed questions as examples for the prompt."""
        if not seed_questions: return ""
        examples = []
        count = 0
        for question, answer in seed_questions.items():
            examples.append(f"Question: {question}\nAnswer: {answer}")
            count += 1
            if count >= 5: break
        if examples:
            # --- Use simple concatenation here too ---
            return ("\nHere are some example questions and answers for this pack and topic:\n\n"
                    + "\n\n".join(examples)
                    + "\n\nUse the instructions and example questions as inspiration, but create entirely new questions that play with wordplay, allusions, and clever phrasing that ties to the topic without being too on-the-nose. Ensure you follow all instructions listed. Above all, the question and answer created must be correct. Do not let style or creativity override accuracy.\n")
        return ""

    async def _process_question_response(
        self,
        response: str,
        pack_id: str,
        pack_topic: str,
        difficulty_str: str
    ) -> List[Dict[str, Any]]:
        """Process the LLM response into structured question data."""
        try:
            target_difficulty = DifficultyLevel(difficulty_str.lower())
        except ValueError:
            logger.warning(f"Invalid target difficulty level '{difficulty_str}', defaulting to MEDIUM")
            target_difficulty = DifficultyLevel.MEDIUM

        questions_data = await parse_json_from_llm(response, [])

        if self.debug_enabled:
            print("\n=== Parsed JSON from LLM ===")
            print(f"Type: {type(questions_data)}")
            print(f"Content: {questions_data}")
            print("============================\n")

        structured_questions = []
        if isinstance(questions_data, list):
            for item in questions_data:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    question_text = clean_text(item["question"])
                    answer_text = clean_text(item["answer"])
                    if not question_text or not answer_text:
                        logger.warning(f"Skipping question with empty content/answer: {item}")
                        continue
                    question_dict = {
                        "question": question_text,
                        "answer": answer_text,
                        "pack_id": pack_id,
                        "pack_topics_item": pack_topic,
                        "difficulty_initial": target_difficulty,
                        "difficulty_current": target_difficulty
                    }
                    structured_questions.append(question_dict)
                    if self.debug_enabled:
                        print(f"Structured question: {json.dumps(question_dict, default=lambda x: x.value if isinstance(x, DifficultyLevel) else str(x))}")
                else:
                    logger.warning(f"Skipping invalid question format in LLM response: {item}")
        else:
            logger.error(f"Failed to parse questions response as a list: {type(questions_data)}")
            if self.debug_enabled:
                print(f"Failed to parse questions response as a list. Type: {type(questions_data)}")

        return structured_questions