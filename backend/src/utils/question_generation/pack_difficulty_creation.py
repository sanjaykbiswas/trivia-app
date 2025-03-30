# backend/src/utils/question_generation/pack_difficulty_creation.py
import uuid
import re
from typing import List, Dict, Optional
from ...models.pack_creation_data import PackCreationDataCreate, PackCreationDataUpdate
from ...repositories.pack_creation_data_repository import PackCreationDataRepository
from ..llm.llm_service import LLMService

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
        # Build prompt for difficulty description generation
        prompt = self._build_difficulty_prompt(creation_name, pack_topics)
        
        # Generate descriptions using LLM
        raw_response = await self.llm_service.generate_content(prompt)
        
        # Parse the response into a dictionary of difficulty levels and descriptions
        difficulty_descriptions = self._parse_difficulty_descriptions(raw_response)
        
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
        topics_text = "\n".join([f"- {topic}" for topic in pack_topics])
        
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
    
    def _parse_difficulty_descriptions(self, llm_response: str) -> Dict[str, str]:
        """
        Parse the LLM response into a dictionary of difficulty levels and descriptions.
        
        Args:
            llm_response: Raw response string from LLM
            
        Returns:
            Dictionary with difficulty levels as keys and descriptions as values
        """
        difficulty_descriptions = {}
        
        # Define the difficulty levels we expect
        expected_difficulties = ["Easy", "Medium", "Hard", "Expert", "Mixed"]
        
        # Split the response by lines
        lines = llm_response.strip().split('\n')
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Try to extract the difficulty level and description
            for difficulty in expected_difficulties:
                if line.lower().startswith(f"{difficulty.lower()}:"):
                    # Extract the description part (after the colon)
                    description = line[len(f"{difficulty}:"):].strip()
                    difficulty_descriptions[difficulty] = description
                    break
        
        # Add any missing difficulties with empty strings
        for difficulty in expected_difficulties:
            if difficulty not in difficulty_descriptions:
                difficulty_descriptions[difficulty] = ""
        
        return difficulty_descriptions
    
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
    
    async def generate_and_store_difficulty_descriptions(self, pack_id: uuid.UUID, creation_name: str, pack_topics: List[str]) -> List[str]:
        """
        Generate, combine, and store difficulty descriptions for a pack in one operation.
        
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