# backend/src/utils/question_generation/custom_instructions_creator.py
"""
Utility for creating custom instructions for trivia question generation.
Provides options to generate instructions using LLM or process manual input.
Uses different LLM prompts based on the presence of seed questions.
"""

from typing import Dict, List, Optional
import logging
# Assuming LLMService and clean_text are correctly imported
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text

# Configure logger
logger = logging.getLogger(__name__)

class CustomInstructionsCreator:
    """
    Utility for creating custom instructions for question generation,
    either by generating them with LLM or handling manual input.
    Uses different prompts depending on whether seed questions are provided.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize with required services.

        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()

    async def generate_custom_instructions(self,
                                         pack_topic: str,
                                         seed_questions: Optional[Dict[str, str]] = None) -> str:
        """
        Generate custom instructions for question generation using LLM.
        The prompt used will differ based on whether seed_questions are provided.

        Args:
            pack_topic: Topic of the trivia pack
            seed_questions: Optional dictionary of example questions and answers

        Returns:
            Generated custom instructions text
        """
        # Build prompt for custom instructions generation - this now contains the conditional logic
        prompt = self._build_instructions_prompt(pack_topic, seed_questions)

        try:
            # Generate instructions using LLM
            # No change needed here, just uses the generated prompt
            raw_response = self.llm_service.generate_content(prompt)
            processed_response = self.llm_service.process_llm_response(raw_response)

            # Log success
            logger.info(f"Successfully generated custom instructions for topic: {pack_topic}")

            return processed_response
        except Exception as e:
            logger.error(f"Error generating custom instructions: {str(e)}")
            # Return an empty string if generation fails
            return ""

    def _format_seed_examples_for_prompt(self, seed_questions: Dict[str, str]) -> str:
        """Helper to format seed questions for inclusion in the prompt."""
        if not seed_questions:
            return "No specific seed questions were provided."

        examples = []
        count = 0
        for question, answer in seed_questions.items():
            examples.append(f"Q: {question}\nA: {answer}")
            count += 1
            if count >= 5: # Limit to 5 examples
                break

        if examples:
            return "Here are some example questions and answers for this topic:\n\n" + "\n\n".join(examples)
        else:
            return "No valid seed questions could be formatted."


    def _build_instructions_prompt(self,
                                 pack_topic: str,
                                 seed_questions: Optional[Dict[str, str]] = None) -> str:
        """
        Build the prompt for custom instructions generation, choosing the template
        based on the presence of seed_questions.

        Args:
            pack_topic: Topic of the trivia pack
            seed_questions: Optional dictionary of example questions and answers

        Returns:
            Formatted prompt string suitable for the LLM
        """
        # --- Conditional Prompt Logic ---
        if seed_questions:
            # --- PROMPT VERSION 1: WITH SEED QUESTIONS ---
            examples_text = self._format_seed_examples_for_prompt(seed_questions)
            prompt = f"""You are being given a trivia topic: '{pack_topic}' and a set of example trivia clues from that category. Your task is to analyze these clues and explain how the category works.

Write a clear, structured description that would help another AI generate new clues that match the same pattern. Your explanation should cover:
- What kind of word or phrase is missing or being asked for in the answer (e.g., adjectives, names, titles, etc.)
- What type of information the clue provides (e.g., plot summary, cultural references, wordplay)
- How the clue leads the player to the answer
- Any consistent patterns in clue phrasing or formatting
- Instructions on how to construct questions if there is an identifiable format that's shown in the seed questions.  If there is variance, encourage variance.
- Limit your response to maximum 5 sentences.

Avoid restating the actual example clues, but use them to extract the underlying logic of the category. Your description should be general enough to guide clue creation but specific enough to preserve the style of the category.

{examples_text}

Your instructions MUST adhere to the following constraints:
1. Should NOT include references to specific difficulty levels (Easy, Medium, Hard, etc.) or adjusting questions based on audience familiarity.
2. Should NOT influence the length of the generated questions.
3. Should NOT guide creation of questions towards styles that are not appropriate for trivia (e.g., subjective opinions, open-ended questions).
4. Should NOT guide creation towards hypotheticals or questions that are not factual.
5. Should NOT try to dissuade from obscurity; obscure facts are acceptable in trivia.

Output Format:
- Sentence 1
- Sentence 2
- Sentence 3
- Sentence 4
- Sentence 5

Do not let style or creativity override accuracy. Respond ONLY with the custom instructions in a clear, direct format. Do not include any other text or markdown formatting (like ```).
"""
        else:
            # --- PROMPT VERSION 2: WITHOUT SEED QUESTIONS ---
            prompt = f"""You need to generate instructions for creating trivia questions for the category: '{pack_topic}'. No example questions are provided.

Your task is to write a clear, structured description based SOLELY on the topic '{pack_topic}' that would help another AI generate good trivia questions. Your description should cover:
- The typical scope and subject matter for this topic in a trivia context.
- Common types of questions or angles associated with '{pack_topic}' (e.g., definitions, key figures, historical events, specific works, technical details).
- Any inherent characteristics of the topic that might influence question style (e.g., is it inherently technical, creative, historical?).
- Potential areas within the topic suitable for trivia questions.
- Limit your response to maximum 5 sentences.

Your instructions MUST adhere to the following constraints:
1. Should NOT include references to specific difficulty levels (Easy, Medium, Hard, etc.) or adjusting questions based on audience familiarity.
2. Should NOT influence the length of the generated questions.
3. Should NOT guide creation of questions towards styles that are not appropriate for trivia (e.g., subjective opinions, open-ended questions).
4. Should NOT guide creation towards hypotheticals or questions that are not factual.
5. Should NOT try to dissuade from obscurity; obscure facts are acceptable in trivia.

Output Format:
- Sentence 1
- Sentence 2
- Sentence 3
- Sentence 4
- Sentence 5

Focus on the nature of the topic itself to provide guidance. Respond ONLY with the custom instructions in a clear, direct format. Do not include any other text or markdown formatting (like ```).
"""
        # --- End Conditional Logic ---

        return prompt

    def process_manual_instructions(self, instructions: str) -> str:
        """
        Process manually provided instructions.
        (No change needed here)

        Args:
            instructions: Manually provided custom instructions

        Returns:
            Processed instructions text
        """
        # Clean and normalize the input
        return clean_text(instructions)