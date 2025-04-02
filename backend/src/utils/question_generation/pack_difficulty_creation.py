# backend/src/utils/question_generation/pack_difficulty_creation.py
import re
from typing import List, Dict, Optional, Any
import logging # Added logging
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text, split_into_chunks

# Configure logger
logger = logging.getLogger(__name__)

class PackDifficultyCreation:
    """
    Utility for generating difficulty descriptions for trivia packs.
    Focuses on LLM interactions for difficulty description creation.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize with required services.

        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()

        # Default base descriptions for each difficulty level
        self.base_descriptions = {
            "Easy": "Should be relatively easy questions that most audiences would know about.",
            "Medium": "Should be of medium difficulty.  Some people may not know about the topic of the question.",
            "Hard": "Should be hard questions that require a deeper understanding of the topic.  Many people may not know the topic, and they should be hard.",
            "Expert": "Questions should be designed for Experts on the topic.  These can be obscure or specialized questions that are genuinely difficult.  There should not be many hints within the question to help get at the answer.",
            "Mixed": "A mix of difficulties spanning easy all the way to obscure or specialized questions that are genuinely difficult.  See the above descriptions for easy, medium, hard, and expert."
        }

    # --- UPDATED METHOD SIGNATURE ---
    async def generate_difficulty_descriptions(self, pack_name: str, pack_topics: List[str]) -> Dict[str, str]:
        """
        Generate custom difficulty descriptions for all levels including mixed.

        Args:
            pack_name: The name of the trivia pack (used instead of creation_name).
            pack_topics: List of topics in the pack.

        Returns:
            Dictionary with difficulty levels as keys and custom descriptions as values.
        """
        # --- END UPDATED SIGNATURE ---
        # Clean and normalize inputs
        pack_name = normalize_text(pack_name, lowercase=False) # Use pack_name
        cleaned_topics = [clean_text(topic) for topic in pack_topics]

        # Build prompt for difficulty description generation (using pack_name)
        prompt = self._build_difficulty_prompt(pack_name, cleaned_topics)

        try: # Added try/except for robustness
            # Generate descriptions using LLM
            raw_response = self.llm_service.generate_content(prompt)
            processed_response = self.llm_service.process_llm_response(raw_response)

            # Parse the response
            difficulty_descriptions = self._parse_difficulty_response(processed_response)

            # Ensure all expected difficulty levels are included
            expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
            for difficulty in expected_difficulties:
                if difficulty not in difficulty_descriptions:
                    logger.warning(f"LLM response did not contain description for '{difficulty}' level for pack '{pack_name}'. Adding empty string.")
                    difficulty_descriptions[difficulty] = ""

            return difficulty_descriptions
        except Exception as e:
             logger.error(f"Error generating difficulty descriptions for pack '{pack_name}': {e}", exc_info=True)
             # Return default descriptions on error
             return {level: "" for level in self.base_descriptions}


    def _parse_difficulty_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the LLM response into a dictionary of difficulty levels and descriptions.
        Handles various formatting inconsistencies.

        Args:
            response_text: Processed response from LLM.

        Returns:
            Dictionary mapping difficulty levels to their descriptions.
        """
        difficulty_descriptions = {}
        expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        response_text = response_text.strip()

        # Attempt to split by newline first, assuming each level is on a new line
        lines = response_text.split('\n')
        processed_levels = set()

        for line in lines:
            line = line.strip()
            if not line: continue

            # Find the first matching difficulty level at the start of the line
            found_level = None
            for level in expected_difficulties:
                if level not in processed_levels:
                    # Match level at the beginning, followed by a colon or space
                    if line.lower().startswith(level.lower() + ":") or line.lower().startswith(level.lower() + " "):
                        # Extract description after the level and separator
                        start_index = len(level)
                        if line[start_index:].startswith(":"):
                            start_index += 1
                        description = line[start_index:].strip()
                        if description:
                            difficulty_descriptions[level] = description
                            found_level = level
                            break # Stop checking levels for this line once one is found

            if found_level:
                processed_levels.add(found_level)

        # If splitting by newline didn't capture all levels, try regex (more robust for messy formats)
        if len(difficulty_descriptions) < len(expected_difficulties):
            logger.debug("Newline splitting incomplete, attempting regex fallback for difficulty parsing.")
            remaining_levels = [level for level in expected_difficulties if level not in difficulty_descriptions]

            for level in remaining_levels:
                # Regex to find the level followed by ':' and capture text until the next level or end of string
                # Lookbehinds ensure we don't match a level name within another description
                pattern = rf"(?<!\w){re.escape(level)}:\s*(.*?)(?=(\n(?<!\w)(?:{'|'.join(expected_difficulties)}):|\Z))"
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                if match:
                    description = match.group(1).strip()
                    # Further clean description: remove potential leading/trailing markdown, quotes etc.
                    description = re.sub(r'^["\'`*-\s]+|["\'`*-\s]+$', '', description)
                    if description:
                        difficulty_descriptions[level] = description

        # Ensure all levels have at least an empty string entry
        for level in expected_difficulties:
            if level not in difficulty_descriptions:
                difficulty_descriptions[level] = ""

        return difficulty_descriptions


    # --- UPDATED METHOD SIGNATURE ---
    def _build_difficulty_prompt(self, pack_name: str, pack_topics: List[str]) -> str:
        """
        Build the prompt for difficulty description generation.

        Args:
            pack_name: Name of the trivia pack (used instead of creation_name).
            pack_topics: List of topics in the pack.

        Returns:
            Formatted prompt string.
        """
        # --- END UPDATED SIGNATURE ---
        # Use split_into_chunks if the topics text might be too long
        topics_text = "\n".join([f"- {topic}" for topic in pack_topics])

        # Only use chunking if the topics text is very long
        if len(topics_text) > 2000:
            chunks = split_into_chunks(topics_text, chunk_size=1500, respect_sentences=True)
            topics_text = chunks[0] + "\n(and additional topics...)"

        prompt = f"""Generate specific difficulty level descriptions for a trivia pack named "{pack_name}"
with the following topics:

{topics_text}

For each difficulty level (Easy, Medium, Hard, Expert, and Mixed), provide a detailed,
pack-specific description of what questions at that level should entail.

The descriptions should:
- Be tailored specifically to "{pack_name}" and its topics
- Explain what makes a question belong to that difficulty level for this specific pack
- Provide clear guidance for question creation at each level
- For the Mixed level, explain how different difficulties would be balanced in this pack

CRITICAL FORMATTING INSTRUCTIONS:
1. DO NOT include any other difficulty level names (Easy, Medium, Hard, Expert, Mixed) within any difficulty description.
2. Each difficulty MUST be on its own separate line with NO other difficulty names in that line's description.
3. Place each description on a SEPARATE LINE from other difficulties.
4. Start each line EXACTLY with the difficulty level name followed by a colon and a space (e.g., "Easy: ").

Format exactly like this (notice each difficulty is on its OWN LINE):

Easy: [description for Easy difficulty]
Medium: [description for Medium difficulty]
Hard: [description for Hard difficulty]
Expert: [description for Expert difficulty]
Mixed: [description for Mixed difficulty]

Example format (EACH ON SEPARATE LINES):

Easy: Questions about basic Roman emperors and common knowledge facts.
Medium: Questions about specific battles and political reforms.
Hard: Questions about lesser-known figures and complex historical events.
Expert: Questions about detailed historical analysis and obscure Roman customs.
Mixed: A balance of questions from all difficulty levels covering various Roman topics.

DO NOT include any explanatory text before or after the difficulty descriptions.
Ensure ONLY the descriptions follow the format above.
"""
        return prompt

    def create_difficulty_json(self, custom_descriptions: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Create a structured JSON object with base and custom descriptions for each difficulty level.

        Args:
            custom_descriptions: Dictionary of custom descriptions by difficulty level.

        Returns:
            Nested dictionary with difficulty levels as keys, each containing a dictionary with 'base' and 'custom' keys.
        """
        difficulty_json = {}

        for level, base_desc in self.base_descriptions.items():
            custom_desc = custom_descriptions.get(level, "")
            difficulty_json[level] = {
                "base": base_desc,
                "custom": custom_desc
            }

        return difficulty_json

    def format_descriptions_for_prompt(self, difficulty_json: Dict[str, Dict[str, str]], difficulties: Optional[List[str]] = None) -> str:
        """
        Format the difficulty descriptions for use in future prompts.

        Args:
            difficulty_json: Nested dictionary of difficulty descriptions.
            difficulties: Optional list of difficulty levels to include (e.g., ["Easy", "Medium"]).
                         If None, all difficulties will be included.

        Returns:
            Formatted string for use in prompts.
        """
        formatted_descriptions = []

        # Ensure consistent order if difficulties is None
        levels_to_include = difficulties if difficulties is not None else ["Easy", "Medium", "Hard", "Expert", "Mixed"]

        for level in levels_to_include:
            if level in difficulty_json:
                descriptions = difficulty_json[level]
                base_desc = descriptions.get("base", "")
                custom_desc = descriptions.get("custom", "")

                # Combine base and custom, prioritizing custom if available
                combined_desc = custom_desc if custom_desc else base_desc
                if combined_desc: # Add only if there is some description
                    # Format as required for the prompt
                    formatted = f"* {level}: {combined_desc}"
                    if not combined_desc.endswith('.'): formatted += '.' # Ensure punctuation
                    formatted_descriptions.append(formatted)

        # Join with newlines
        return "\n".join(formatted_descriptions)

    def _get_default_difficulty_structure(self) -> Dict[str, Dict[str, str]]:
        """
        Get the default difficulty structure with empty custom descriptions.

        Returns:
            Default nested dictionary with base descriptions.
        """
        return {level: {"base": base_desc, "custom": ""} for level, base_desc in self.base_descriptions.items()}