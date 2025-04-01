# backend/src/utils/question_generation/pack_difficulty_creation.py
import re
from typing import List, Dict, Optional, Any
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text, split_into_chunks

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
            "Mixed": "A mix of difficulties spanning relatively easy all the way to obscure or specialized questions that are genuinely difficult."
        }
    
    async def generate_difficulty_descriptions(self, creation_name: str, pack_topics: List[str]) -> Dict[str, str]:
        """
        Generate custom difficulty descriptions for all levels including mixed.
        
        Args:
            creation_name: The name of the trivia pack
            pack_topics: List of topics in the pack
            
        Returns:
            Dictionary with difficulty levels as keys and custom descriptions as values
        """
        # Clean and normalize inputs
        creation_name = normalize_text(creation_name, lowercase=False)
        cleaned_topics = [clean_text(topic) for topic in pack_topics]
        
        # Build prompt for difficulty description generation
        prompt = self._build_difficulty_prompt(creation_name, cleaned_topics)
        
        # Generate descriptions using LLM (CHANGED: removed await)
        raw_response = self.llm_service.generate_content(prompt)
        processed_response = self.llm_service.process_llm_response(raw_response)
        
        # Parse the response
        difficulty_descriptions = self._parse_difficulty_response(processed_response)
        
        # Ensure all expected difficulty levels are included
        expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        for difficulty in expected_difficulties:
            if difficulty not in difficulty_descriptions:
                difficulty_descriptions[difficulty] = ""
        
        return difficulty_descriptions
    
    def _parse_difficulty_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse the LLM response into a dictionary of difficulty levels and descriptions.
        
        Args:
            response_text: Processed response from LLM
            
        Returns:
            Dictionary mapping difficulty levels to their descriptions
        """
        difficulty_descriptions = {}
        expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        
        # Split the text by difficulty level markers
        parts = {}
        for i in range(len(expected_difficulties)):
            current_level = expected_difficulties[i]
            next_levels = []
            
            # Add all potential next levels that could follow the current one
            for j in range(len(expected_difficulties)):
                if i != j:  # Don't include the current level
                    next_levels.append(expected_difficulties[j])
            
            # Create a pattern to find the current level and capture everything until the next level
            if next_levels:
                marker_pattern = r'(?:^|\s|[;:])' + re.escape(current_level) + r'[;:]?\s*(.*?)(?=(?:\s|^)(?:' + '|'.join(map(re.escape, next_levels)) + r')[;:]|\Z)'
            else:
                marker_pattern = r'(?:^|\s|[;:])' + re.escape(current_level) + r'[;:]?\s*(.*?)(?=\Z)'
            
            matches = re.findall(marker_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            if matches:
                # Get the first match that contains content
                for match in matches:
                    content = match.strip()
                    
                    # Clean up the content
                    content = re.sub(r'\\+\s*$', '', content)
                    
                    # Remove any difficulty level markers that might be in the content
                    for level in expected_difficulties:
                        content = re.sub(r'\\+\s*' + re.escape(level) + r':', '', content)
                    
                    if content:
                        parts[current_level] = content
                        break
        
        # Process the extracted parts
        for level in expected_difficulties:
            if level in parts:
                difficulty_descriptions[level] = parts[level]
            else:
                difficulty_descriptions[level] = ""
        
        return difficulty_descriptions
    
    def _build_difficulty_prompt(self, creation_name: str, pack_topics: List[str]) -> str:
        """
        Build the prompt for difficulty description generation.
        
        Args:
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            
        Returns:
            Formatted prompt string
        """
        # Use split_into_chunks if the topics text might be too long
        topics_text = "\n".join([f"- {topic}" for topic in pack_topics])
        
        # Only use chunking if the topics text is very long
        if len(topics_text) > 2000:
            chunks = split_into_chunks(topics_text, chunk_size=1500, respect_sentences=True)
            topics_text = chunks[0] + "\n(and additional topics...)"
        
        prompt = f"""Generate specific difficulty level descriptions for a trivia pack named "{creation_name}" 
with the following topics:

{topics_text}

For each difficulty level (Easy, Medium, Hard, Expert, and Mixed), provide a detailed, 
pack-specific description of what questions at that level should entail.

The descriptions should:
- Be tailored specifically to "{creation_name}" and its topics
- Explain what makes a question belong to that difficulty level for this specific pack
- Provide clear guidance for question creation at each level
- For the Mixed level, explain how different difficulties would be balanced in this pack

CRITICAL FORMATTING INSTRUCTIONS:
1. DO NOT include any other difficulty level names (Easy, Medium, Hard, Expert, Mixed) within any difficulty description
2. Each difficulty MUST be on its own separate line with NO other difficulty names in that line's description
3. Place each description on a SEPARATE LINE from other difficulties

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
DO NOT include any other difficulty names within a difficulty description.
"""
        return prompt
    
    def create_difficulty_json(self, custom_descriptions: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Create a structured JSON object with base and custom descriptions for each difficulty level.
        
        Args:
            custom_descriptions: Dictionary of custom descriptions by difficulty level
            
        Returns:
            Nested dictionary with difficulty levels as keys, each containing a dictionary with 'base' and 'custom' keys
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
            difficulty_json: Nested dictionary of difficulty descriptions
            difficulties: Optional list of difficulty levels to include (e.g., ["Easy", "Medium"])
                         If None, all difficulties will be included
            
        Returns:
            Formatted string for use in prompts
        """
        formatted_descriptions = []
        
        for level, descriptions in difficulty_json.items():
            # Skip this difficulty if it's not in the requested list
            if difficulties is not None and level not in difficulties:
                continue
                
            base_desc = descriptions.get("base", "")
            custom_desc = descriptions.get("custom", "")
            
            # Format as required for the prompt
            formatted = f"* {level}: {base_desc}. {custom_desc}."
            formatted_descriptions.append(formatted)
        
        # Join with newlines
        return "\n".join(formatted_descriptions)
    
    def _get_default_difficulty_structure(self) -> Dict[str, Dict[str, str]]:
        """
        Get the default difficulty structure with empty custom descriptions.
        
        Returns:
            Default nested dictionary with base descriptions
        """
        return {level: {"base": base_desc, "custom": ""} for level, base_desc in self.base_descriptions.items()}