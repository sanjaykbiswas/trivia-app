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
        prompt = f"""Generate custom instructions for creating trivia questions about {pack_topic}.

Based on the the topic: {pack_topic} and the following question examples, come up with customized instructions to give an LLM to create additional questions.

{examples_text}

Your instructions should cover:
1. The style and tone of questions (e.g., straightforward, playful, challenging)
2. The level of specificity expected in questions and answers
3. Any nuanced aspects of {pack_topic} to focus on
4. Any formats or structures that work well for questions about this topic
5. Any potential pitfalls or areas to avoid

The instructions should be specific to {pack_topic} and reflect the style of any example questions provided.

Respond ONLY with the custom instructions in a clear, direct format. Do not include any other text.
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