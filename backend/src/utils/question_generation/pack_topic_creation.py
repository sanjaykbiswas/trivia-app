# backend/src/utils/question_generation/pack_topic_creation.py
import logging
from typing import List, Optional
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text
from ..llm.llm_parsing_utils import parse_json_from_llm

# Setup logger
logger = logging.getLogger(__name__)

class PackTopicCreation:
    """
    Utility for generating pack topics for trivia question generation.
    Focuses on LLM interaction for topic creation.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize with required services.
        
        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()
        
    async def create_pack_topics(self, creation_name: str, 
                               num_topics: int = 5) -> List[str]:
        """
        Create a list of topics for a trivia pack using LLM.
        
        Args:
            creation_name: The name of the trivia pack
            num_topics: Number of topics to generate
            
        Returns:
            List of generated topics
        """
        # Clean and normalize inputs using document_processing utilities
        creation_name = normalize_text(creation_name, lowercase=False)
        
        # Generate the prompt for topic creation
        prompt = self._build_topic_generation_prompt(
            creation_name=creation_name,
            num_topics=num_topics
        )
        
        # Generate topics using LLM - single call
        raw_response = await self.llm_service.generate_content(prompt)
        
        # Parse the raw response directly into JSON
        default_topics = []  # Default in case parsing fails
        topics_data = parse_json_from_llm(raw_response, default_topics)
        
        # Validate the result is a list of strings
        if isinstance(topics_data, list):
            # Convert any non-string items to strings
            topics = [str(item) for item in topics_data if item]
        else:
            topics = default_topics
        
        # Ensure we have the requested number of topics (truncate if we have too many)
        if len(topics) > num_topics:
            topics = topics[:num_topics]
            
        # Check if we got fewer topics than requested and output a warning
        if len(topics) < num_topics:
            logger.warning(
                f"Requested {num_topics} topics for '{creation_name}', but only received {len(topics)}. "
                f"Continuing with the available topics."
            )
            print(f"Warning: Requested {num_topics} topics but only got {len(topics)}")
        
        return topics
    
    def _build_topic_generation_prompt(self, creation_name: str, 
                                      num_topics: int = 5) -> str:
        """
        Build the prompt for topic creation.
        
        Args:
            creation_name: Name of the trivia pack
            num_topics: Number of topics to generate
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Generate {num_topics} specific topics for a trivia pack named "{creation_name}".

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}

IMPORTANT: Return the topics as a valid JSON array of strings in this exact format:
[
  "Topic 1",
  "Topic 2",
  "Topic 3"
]

For example, if the pack name was "World Geography", the response should be:
[
  "Mountain ranges across continents",
  "Island nations and archipelagos",
  "Capital cities of the world",
  "Major rivers and watersheds",
  "Desert ecosystems"
]

DO NOT include any additional text, explanations, or markdown - ONLY return the JSON array.
"""
        return prompt
    
    async def create_additional_topics(self, existing_topics: List[str], 
                                     creation_name: str,
                                     num_additional_topics: int = 3) -> List[str]:
        """
        Create additional topics that don't overlap with existing ones.
        
        Args:
            existing_topics: List of existing topics to avoid duplicating
            creation_name: The name of the trivia pack
            num_additional_topics: Number of new topics to add
            
        Returns:
            List of new topics
        """
        # Build prompt for additional topics
        additional_prompt = f"""Generate {num_additional_topics} new specific topics for a trivia pack named "{creation_name}".
        
Please provide topics DIFFERENT from these existing topics:
{', '.join(existing_topics)}

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {creation_name}

IMPORTANT: Return the topics as a valid JSON array of strings in this exact format:
[
  "New Topic 1",
  "New Topic 2",
  "New Topic 3"
]

DO NOT include any additional text, explanations, or markdown - ONLY return the JSON array.
"""
        
        # Generate additional topics - single call
        raw_response = await self.llm_service.generate_content(additional_prompt)
        
        # Parse the raw response directly into JSON
        default_topics = []
        new_topics_data = parse_json_from_llm(raw_response, default_topics)
        
        # Validate the result is a list of strings
        if isinstance(new_topics_data, list):
            new_topics = [str(item) for item in new_topics_data if item]
        else:
            new_topics = default_topics
            
        # Check if we got fewer topics than requested and output a warning
        if len(new_topics) < num_additional_topics:
            logger.warning(
                f"Requested {num_additional_topics} additional topics for '{creation_name}', "
                f"but only received {len(new_topics)}. Continuing with available topics."
            )
            print(f"Warning: Requested {num_additional_topics} additional topics but only got {len(new_topics)}")
        
        return new_topics