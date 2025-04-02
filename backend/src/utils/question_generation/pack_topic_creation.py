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

    # --- UPDATED METHOD SIGNATURE ---
    async def create_pack_topics(self, pack_name: str,
                               num_topics: int = 5,
                               predefined_topic: Optional[str] = None) -> List[str]:
        """
        Create a list of topics for a trivia pack using LLM.

        Args:
            pack_name: The name of the trivia pack (used instead of creation_name).
            num_topics: Number of topics to generate.
            predefined_topic: Optional predefined topic to use instead of generation.

        Returns:
            List of topics (either generated or containing the predefined topic).
        """
        # --- END UPDATED SIGNATURE ---
        # If a predefined topic is provided, use it directly
        if predefined_topic:
            clean_topic = normalize_text(predefined_topic, lowercase=False)
            logger.info(f"Using predefined topic: {clean_topic}")
            return [clean_topic]

        # Clean and normalize inputs
        pack_name = normalize_text(pack_name, lowercase=False) # Use pack_name

        # Generate the prompt for topic creation (using pack_name)
        prompt = self._build_topic_generation_prompt(
            pack_name=pack_name,
            num_topics=num_topics
        )

        try: # Added try/except
            # Generate topics using LLM
            raw_response = self.llm_service.generate_content(prompt)

            # Parse the raw response directly into JSON
            default_topics = []
            topics_data = await parse_json_from_llm(raw_response, default_topics)

            # Validate the result is a list of strings
            if isinstance(topics_data, list):
                topics = [str(item) for item in topics_data if item] # Filter out empty strings
            else:
                logger.warning(f"LLM topic generation for '{pack_name}' returned non-list data: {type(topics_data)}. Using empty list.")
                topics = default_topics

            # Ensure we have the requested number of topics (truncate if too many)
            if len(topics) > num_topics:
                topics = topics[:num_topics]

            # Check if we got fewer topics than requested
            if len(topics) < num_topics:
                logger.warning(
                    f"Requested {num_topics} topics for '{pack_name}', but only received {len(topics)}. "
                    f"Continuing with available topics."
                )
                print(f"Warning: Requested {num_topics} topics but only got {len(topics)}")

            return topics
        except Exception as e:
             logger.error(f"Error generating topics for pack '{pack_name}': {e}", exc_info=True)
             return [] # Return empty list on error


    # --- UPDATED METHOD SIGNATURE ---
    def _build_topic_generation_prompt(self, pack_name: str,
                                      num_topics: int = 5) -> str:
        """
        Build the prompt for topic creation.

        Args:
            pack_name: Name of the trivia pack (used instead of creation_name).
            num_topics: Number of topics to generate.

        Returns:
            Formatted prompt string.
        """
        # --- END UPDATED SIGNATURE ---
        prompt = f"""Generate {num_topics} specific topics for a trivia pack named "{pack_name}".

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {pack_name}
- They should be wide enough that there is room for a variety of interesting questions to be generated about the topic

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

    # --- UPDATED METHOD SIGNATURE ---
    async def create_additional_topics(self, existing_topics: List[str],
                                     pack_name: str,
                                     num_additional_topics: int = 3,
                                     predefined_topic: Optional[str] = None) -> List[str]:
        """
        Create additional topics that don't overlap with existing ones.

        Args:
            existing_topics: List of existing topics to avoid duplicating.
            pack_name: The name of the trivia pack (used instead of creation_name).
            num_additional_topics: Number of new topics to add.
            predefined_topic: Optional predefined topic to add directly.

        Returns:
            List of new topics.
        """
        # --- END UPDATED SIGNATURE ---
        # If a predefined topic is provided, use it directly
        if predefined_topic:
            clean_topic = normalize_text(predefined_topic, lowercase=False)
            if clean_topic in existing_topics:
                logger.warning(f"Predefined topic '{clean_topic}' already exists in topics list")
                return []
            logger.info(f"Adding predefined topic: {clean_topic}")
            return [clean_topic]

        # Clean pack name
        pack_name = normalize_text(pack_name, lowercase=False) # Use pack_name

        # Build prompt for additional topics (using pack_name)
        additional_prompt = f"""Generate {num_additional_topics} new specific topics for a trivia pack named "{pack_name}".

Please provide topics DIFFERENT from these existing topics:
{', '.join(existing_topics)}

The topics should:
- Be specific enough to generate interesting trivia questions
- Cover different aspects related to {pack_name}

IMPORTANT: Return the topics as a valid JSON array of strings in this exact format:
[
  "New Topic 1",
  "New Topic 2",
  "New Topic 3"
]

DO NOT include any additional text, explanations, or markdown - ONLY return the JSON array.
"""

        try: # Added try/except
            # Generate additional topics
            raw_response = self.llm_service.generate_content(additional_prompt)

            # Parse the raw response directly into JSON
            default_topics = []
            new_topics_data = await parse_json_from_llm(raw_response, default_topics)

            # Validate the result is a list of strings
            if isinstance(new_topics_data, list):
                new_topics = [str(item) for item in new_topics_data if item] # Filter empty strings
            else:
                logger.warning(f"LLM additional topic generation for '{pack_name}' returned non-list data: {type(new_topics_data)}. Using empty list.")
                new_topics = default_topics

            # Check if we got fewer topics than requested
            if len(new_topics) < num_additional_topics:
                logger.warning(
                    f"Requested {num_additional_topics} additional topics for '{pack_name}', "
                    f"but only received {len(new_topics)}. Continuing with available topics."
                )
                print(f"Warning: Requested {num_additional_topics} additional topics but only got {len(new_topics)}")

            # Filter out any topics that might *still* duplicate existing ones (LLM might ignore instructions)
            final_new_topics = [topic for topic in new_topics if topic not in existing_topics]
            if len(final_new_topics) < len(new_topics):
                logger.warning(f"Filtered out {len(new_topics) - len(final_new_topics)} additional topics that already existed.")

            return final_new_topics
        except Exception as e:
             logger.error(f"Error generating additional topics for pack '{pack_name}': {e}", exc_info=True)
             return [] # Return empty list on error