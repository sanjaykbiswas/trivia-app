# backend/src/utils/question_generation/pack_difficulty_creation.py
import uuid
import re
import json
from typing import List, Dict, Optional, Any
from ...models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text, split_into_chunks

class PackDifficultyCreation:
    """
    Handles the creation and management of difficulty descriptions for trivia packs.
    """
    
    def __init__(self, 
                 pack_creation_data_repository: PackCreationDataRepository, 
                 llm_service: Optional[LLMService] = None):
        """
        Initialize with required repositories and services.
        
        Args:
            pack_creation_data_repository: Repository for pack creation data operations
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.pack_creation_repository = pack_creation_data_repository
        self.llm_service = llm_service or LLMService()
        
        # Default base descriptions for each difficulty level
        self.base_descriptions = {
            "Easy": "Should be easy topics about the topic.",
            "Medium": "Should be medium topics about the topic.",
            "Hard": "Should be hard topics about the topic.",
            "Expert": "Questions should be designed for Experts on the topic.",
            "Mixed": "A mix of difficulties."
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
        
        # Generate descriptions using LLM
        raw_response = await self.llm_service.generate_content(prompt)
        processed_response = await self.llm_service.process_llm_response(raw_response)
        
        # Parse the response - using improved parsing logic
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
    
    async def store_difficulty_descriptions(self, pack_id: uuid.UUID, difficulty_json: Dict[str, Dict[str, str]]) -> None:
        """
        Store difficulty descriptions in JSON format in the pack_creation_data table.
        
        Args:
            pack_id: UUID of the pack
            difficulty_json: Nested dictionary of difficulty descriptions
        """
        # Convert dictionary to JSON string to store in the database
        difficulty_json_str = json.dumps(difficulty_json)
        
        # Check if there's already data for this pack
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if existing_data:
            # Update existing record with JSON string
            update_data = PackCreationDataUpdate(
                custom_difficulty_description=difficulty_json_str
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
        else:
            # For this scenario, we expect pack_creation_data to already exist
            # (created in the topic creation phase), but just in case:
            print(f"Warning: No existing pack creation data found for pack_id {pack_id}")
            # We would need additional information to create a new record
    
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
    
    async def get_existing_difficulty_descriptions(self, pack_id: uuid.UUID) -> Dict[str, Dict[str, str]]:
        """
        Retrieve existing difficulty descriptions for a pack.
        
        Args:
            pack_id: UUID of the pack
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'custom_difficulty_description'):
            # Get the stored data
            stored_data = creation_data.custom_difficulty_description
            
            # Check if the stored data is in JSON format (string)
            if isinstance(stored_data, str):
                try:
                    return json.loads(stored_data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, return empty structure
                    print(f"Warning: Invalid JSON format in custom_difficulty_description for pack_id {pack_id}")
                    return self._get_default_difficulty_structure()
            elif isinstance(stored_data, dict):
                # It's already a dictionary (might happen if already parsed by Pydantic)
                return stored_data
        
        # Return default structure if no data found
        return self._get_default_difficulty_structure()
    
    def _get_default_difficulty_structure(self) -> Dict[str, Dict[str, str]]:
        """
        Get the default difficulty structure with empty custom descriptions.
        
        Returns:
            Default nested dictionary with base descriptions
        """
        return {level: {"base": base_desc, "custom": ""} for level, base_desc in self.base_descriptions.items()}
    
    async def update_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        difficulty_updates: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Update specific difficulty descriptions without replacing all of them.
        
        Args:
            pack_id: UUID of the pack
            difficulty_updates: Dictionary mapping difficulty levels to their new custom descriptions
                               (e.g., {"Hard": "New hard description", "Expert": "New expert description"})
            
        Returns:
            Updated nested dictionary of difficulty descriptions
        """
        # Get existing descriptions
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # Update only the specified difficulty levels
        for level, new_custom_desc in difficulty_updates.items():
            if level in existing_descriptions:
                existing_descriptions[level]["custom"] = new_custom_desc
            else:
                # If level doesn't exist yet, create it with default base description
                base_desc = self.base_descriptions.get(level, "")
                existing_descriptions[level] = {
                    "base": base_desc,
                    "custom": new_custom_desc
                }
        
        # Store updated descriptions
        await self.store_difficulty_descriptions(pack_id, existing_descriptions)
        
        return existing_descriptions
    
    async def generate_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        creation_name: str,
        pack_topics: List[str],
        difficulty_levels: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate descriptions for specific difficulty levels and update them while preserving others.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"])
            
        Returns:
            Updated nested dictionary of difficulty descriptions
        """
        # Get existing descriptions first
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # Generate all difficulty descriptions (temporary)
        all_descriptions = await self.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )
        
        # Extract only the requested difficulty levels
        updates = {level: all_descriptions.get(level, "") for level in difficulty_levels if level in all_descriptions}
        
        # Update only the specified levels
        return await self.update_specific_difficulty_descriptions(
            pack_id=pack_id,
            difficulty_updates=updates
        )
        
    async def generate_and_store_difficulty_descriptions(self, pack_id: uuid.UUID, creation_name: str, pack_topics: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Generate and store difficulty descriptions for a pack in JSON format.
        This will overwrite any existing difficulty descriptions.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        # Generate custom descriptions
        custom_descriptions = await self.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )
        
        # Convert to JSON structure
        difficulty_json = self.create_difficulty_json(custom_descriptions)
        
        # Store in database
        await self.store_difficulty_descriptions(
            pack_id=pack_id,
            difficulty_json=difficulty_json
        )
        
        return difficulty_json
    
    async def generate_and_handle_existing_difficulty_descriptions(
        self, 
        pack_id: uuid.UUID, 
        creation_name: str, 
        pack_topics: List[str],
        force_regenerate: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """
        Handles the generation of difficulty descriptions while respecting existing ones.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            force_regenerate: If True, will regenerate descriptions even if they exist
            
        Returns:
            Nested dictionary of difficulty descriptions
        """
        # Check if difficulty descriptions already exist
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # Check if we have any custom descriptions
        has_custom_descriptions = False
        for level_data in existing_descriptions.values():
            if level_data.get("custom", ""):
                has_custom_descriptions = True
                break
        
        # If descriptions exist and we don't want to regenerate, return them
        if has_custom_descriptions and not force_regenerate:
            return existing_descriptions
        
        # Otherwise, generate new descriptions
        return await self.generate_and_store_difficulty_descriptions(
            pack_id=pack_id,
            creation_name=creation_name,
            pack_topics=pack_topics
        )