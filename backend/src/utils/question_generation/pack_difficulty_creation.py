# backend/src/utils/question_generation/pack_difficulty_creation.py
import uuid
import re
from typing import List, Dict, Optional
from ...models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ..llm.llm_service import LLMService
from ..document_processing.processors import clean_text, normalize_text, split_into_chunks
from ..llm.llm_parsing_utils import extract_key_value_pairs

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
        
        # Parse the response into a dictionary of difficulty levels and descriptions
        # Using the new extract_key_value_pairs utility
        difficulty_descriptions = extract_key_value_pairs(processed_response)
        
        # Ensure all expected difficulty levels are included
        expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        for difficulty in expected_difficulties:
            if difficulty not in difficulty_descriptions:
                difficulty_descriptions[difficulty] = ""
        
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

Please format your response exactly as follows, with each difficulty on a new line:
Easy: [custom description for easy questions]
Medium: [custom description for medium questions]
Hard: [custom description for hard questions]
Expert: [custom description for expert questions]
Mixed: [custom description for mixed difficulty]

Return ONLY these formatted descriptions with no additional text.
"""
        return prompt
    
    def create_combined_difficulty_descriptions(self, custom_descriptions: Dict[str, str]) -> List[str]:
        """
        Combine base descriptions with custom descriptions in the required format.
        
        Args:
            custom_descriptions: Dictionary of custom descriptions by difficulty level
            
        Returns:
            List of combined descriptions in the format: "Level; Base Description; Custom Description"
        """
        combined_descriptions = []
        
        for level, base_desc in self.base_descriptions.items():
            custom_desc = custom_descriptions.get(level, "")
            combined_description = f"{level}; {base_desc}; {custom_desc}"
            combined_descriptions.append(combined_description)
        
        return combined_descriptions
    
    async def store_difficulty_descriptions(self, pack_id: uuid.UUID, combined_descriptions: List[str]) -> None:
        """
        Store combined difficulty descriptions in the pack_creation_data table.
        If difficulty descriptions already exist for this pack, they will be overwritten.
        
        Args:
            pack_id: UUID of the pack
            combined_descriptions: List of combined descriptions to store
        """
        # Check if there's already data for this pack
        existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if existing_data:
            # Update existing record
            update_data = PackCreationDataUpdate(
                custom_difficulty_description=combined_descriptions
            )
            await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
        else:
            # For this scenario, we expect pack_creation_data to already exist
            # (created in the topic creation phase), but just in case:
            print(f"Warning: No existing pack creation data found for pack_id {pack_id}")
            # We would need additional information to create a new record
    
    def format_descriptions_for_prompt(self, combined_descriptions: List[str], difficulties: Optional[List[str]] = None) -> str:
        """
        Format the combined descriptions for use in future prompts.
        
        Args:
            combined_descriptions: List of combined descriptions
            difficulties: Optional list of difficulty levels to include (e.g., ["Easy", "Medium"])
                         If None, all difficulties will be included
            
        Returns:
            Formatted string for use in prompts
        """
        formatted_descriptions = []
        
        for description in combined_descriptions:
            # Split the combined description into its components
            parts = description.split(";")
            if len(parts) >= 3:
                level = parts[0].strip()
                
                # Skip this difficulty if it's not in the requested list
                if difficulties is not None and level not in difficulties:
                    continue
                    
                base_desc = parts[1].strip()
                custom_desc = parts[2].strip()
                
                # Format as required for the prompt
                formatted = f"* {level}: {base_desc}. {custom_desc}."
                formatted_descriptions.append(formatted)
        
        # Join with newlines
        return "\n".join(formatted_descriptions)
    
    async def get_existing_difficulty_descriptions(self, pack_id: uuid.UUID) -> List[str]:
        """
        Retrieve existing difficulty descriptions for a pack.
        
        Args:
            pack_id: UUID of the pack
            
        Returns:
            List of existing difficulty descriptions
        """
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'custom_difficulty_description'):
            return creation_data.custom_difficulty_description
        else:
            return []
    
    def parse_difficulty_descriptions(self, combined_descriptions: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Parse combined difficulty descriptions into a structured dictionary.
        
        Args:
            combined_descriptions: List of combined descriptions in format "Level; Base Description; Custom Description"
            
        Returns:
            Dictionary with difficulty levels as keys, each containing a dictionary with 'base' and 'custom' keys
        """
        parsed_descriptions = {}
        
        for description in combined_descriptions:
            parts = description.split(";")
            if len(parts) >= 3:
                level = parts[0].strip()
                base_desc = parts[1].strip()
                custom_desc = parts[2].strip()
                
                parsed_descriptions[level] = {
                    'base': base_desc,
                    'custom': custom_desc
                }
                
        return parsed_descriptions
    
    async def update_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        difficulty_updates: Dict[str, str]
    ) -> List[str]:
        """
        Update specific difficulty descriptions without replacing all of them.
        
        Args:
            pack_id: UUID of the pack
            difficulty_updates: Dictionary mapping difficulty levels to their new custom descriptions
                               (e.g., {"Hard": "New hard description", "Expert": "New expert description"})
            
        Returns:
            Updated list of combined difficulty descriptions
            
        Raises:
            ValueError: If no existing difficulty descriptions are found for the pack
        """
        # Get existing descriptions
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        if not existing_descriptions:
            raise ValueError(f"No existing difficulty descriptions found for pack_id {pack_id}")
        
        # Parse existing descriptions
        parsed_descriptions = self.parse_difficulty_descriptions(existing_descriptions)
        
        # Update only the specified difficulty levels
        for level, new_custom_desc in difficulty_updates.items():
            if level in parsed_descriptions:
                parsed_descriptions[level]['custom'] = new_custom_desc
            else:
                # If level doesn't exist yet, create it with default base description
                base_desc = self.base_descriptions.get(level, "")
                parsed_descriptions[level] = {
                    'base': base_desc,
                    'custom': new_custom_desc
                }
        
        # Reconstruct combined descriptions
        updated_descriptions = []
        for level, descriptions in parsed_descriptions.items():
            combined = f"{level}; {descriptions['base']}; {descriptions['custom']}"
            updated_descriptions.append(combined)
        
        # Store updated descriptions
        await self.store_difficulty_descriptions(pack_id, updated_descriptions)
        
        return updated_descriptions
    
    async def generate_specific_difficulty_descriptions(
        self,
        pack_id: uuid.UUID,
        creation_name: str,
        pack_topics: List[str],
        difficulty_levels: List[str]
    ) -> List[str]:
        """
        Generate descriptions for specific difficulty levels and update them while preserving others.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"])
            
        Returns:
            Updated list of combined difficulty descriptions
            
        Raises:
            ValueError: If no existing difficulty descriptions are found for the pack
        """
        # Get existing descriptions first
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        if not existing_descriptions:
            # If no existing descriptions, generate all of them
            return await self.generate_and_store_difficulty_descriptions(
                pack_id=pack_id,
                creation_name=creation_name,
                pack_topics=pack_topics
            )
        
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
        
    async def generate_and_store_difficulty_descriptions(self, pack_id: uuid.UUID, creation_name: str, pack_topics: List[str]) -> List[str]:
        """
        Generate, combine, and store difficulty descriptions for a pack in one operation.
        This will overwrite any existing difficulty descriptions.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            
        Returns:
            List of combined difficulty descriptions
        """
        # Generate custom descriptions
        custom_descriptions = await self.generate_difficulty_descriptions(
            creation_name=creation_name,
            pack_topics=pack_topics
        )
        
        # Combine with base descriptions
        combined_descriptions = self.create_combined_difficulty_descriptions(custom_descriptions)
        
        # Store in database
        await self.store_difficulty_descriptions(
            pack_id=pack_id,
            combined_descriptions=combined_descriptions
        )
        
        return combined_descriptions
    
    async def generate_and_handle_existing_difficulty_descriptions(
        self, 
        pack_id: uuid.UUID, 
        creation_name: str, 
        pack_topics: List[str],
        force_regenerate: bool = False
    ) -> List[str]:
        """
        Handles the generation of difficulty descriptions while respecting existing ones.
        
        Args:
            pack_id: UUID of the pack
            creation_name: Name of the trivia pack
            pack_topics: List of topics in the pack
            force_regenerate: If True, will regenerate descriptions even if they exist
            
        Returns:
            List of combined difficulty descriptions
        """
        # Check if difficulty descriptions already exist
        existing_descriptions = await self.get_existing_difficulty_descriptions(pack_id)
        
        # If descriptions exist and we don't want to regenerate, return them
        if existing_descriptions and not force_regenerate:
            return existing_descriptions
        
        # Otherwise, generate new descriptions
        return await self.generate_and_store_difficulty_descriptions(
            pack_id=pack_id,
            creation_name=creation_name,
            pack_topics=pack_topics
        )