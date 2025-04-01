# backend/src/utils/question_generation/custom_instructions_creator.py
"""
Utility for creating custom instructions for trivia question generation.
Provides options to generate instructions using LLM or process manual input.
"""

from typing import Dict, List, Optional
import logging
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text

# Configure logger
logger = logging.getLogger(__name__)

class CustomInstructionsCreator:
    """
    Utility for creating custom instructions for question generation,
    either by generating them with LLM or handling manual input.
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
                                         seed_questions: Dict[str, str] = None) -> str:
        """
        Generate custom instructions for question generation using LLM.
        
        Args:
            pack_topic: Topic of the trivia pack
            seed_questions: Dictionary of example questions and answers
            
        Returns:
            Generated custom instructions text
        """
        # Build prompt for custom instructions generation
        prompt = self._build_instructions_prompt(pack_topic, seed_questions)
        
        try:
            # Generate instructions using LLM
            raw_response = self.llm_service.generate_content(prompt)
            processed_response = self.llm_service.process_llm_response(raw_response)
            
            # Log success
            logger.info(f"Successfully generated custom instructions for topic: {pack_topic}")
            
            return processed_response
        except Exception as e:
            logger.error(f"Error generating custom instructions: {str(e)}")
            # Return an empty string if generation fails
            return ""
    
    def _build_instructions_prompt(self, 
                                 pack_topic: str, 
                                 seed_questions: Dict[str, str] = None) -> str:
        """
        Build the prompt for custom instructions generation.
        
        Args:
            pack_topic: Topic of the trivia pack
            seed_questions: Dictionary of example questions and answers
            
        Returns:
            Formatted prompt string
        """
        # Format seed questions as examples if provided
        examples_text = ""
        if seed_questions and len(seed_questions) > 0:
            examples = []
            # Limit to 5 examples to keep prompt concise
            count = 0
            for question, answer in seed_questions.items():
                examples.append(f"Q: {question}\nA: {answer}")
                count += 1
                if count >= 5:
                    break
            
            if examples:
                examples_text = "Here are some example questions and answers for this topic:\n\n" + "\n\n".join(examples)
        
        # Build the prompt
        prompt = f"""You are being given a trivia topic: '{pack_topic}' and a set of example trivia clues from that category. Your task is to analyze these clues and explain how the category works.

Write a clear, structured description that would help another AI generate new clues that match the same pattern. Your explanation should cover:
- What kind of word or phrase is missing or being asked for in the answer (e.g., adjectives, names, titles, etc.)
- What type of information the clue provides (e.g., plot summary, cultural references, wordplay)
- How the clue leads the player to the answer
- Any consistent patterns in clue phrasing or formatting
- How difficulty seems to vary across the clues

Avoid restating the actual example clues, but use them to extract the underlying logic of the category. Your description should be general enough to guide clue creation but specific enough to preserve the style of the category.

Here are the examples:

{examples_text}

Your instructions:
1. Should not define specificity levels
2. Should not include references to difficulty levels or adjusting questions based on audience familiarity with a topic
3. Should not influence the length of the question
4. Should not guide creation of questions towards styles that are not appropriate for trivia
5. Should not guide creation towards hypotheticals or questions that are not factual
6. Should not try to dissuade from obscurity

Do not let style or creativity override accuracy.  Respond ONLY with the custom instructions in a clear, direct format. Do not include any other text.
"""
        return prompt
    
    def process_manual_instructions(self, instructions: str) -> str:
        """
        Process manually provided instructions.
        
        Args:
            instructions: Manually provided custom instructions
            
        Returns:
            Processed instructions text
        """
        # Clean and normalize the input
        return clean_text(instructions)