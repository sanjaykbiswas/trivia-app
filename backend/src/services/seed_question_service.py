# backend/src/services/seed_question_service.py
import logging
from typing import Dict, Optional

from ..models.pack_creation_data import PackCreationDataUpdate
from ..repositories.pack_creation_data_repository import PackCreationDataRepository
from ..utils.question_generation.seed_question_processor import SeedQuestionProcessor
from ..utils.question_generation.custom_instructions_creator import CustomInstructionsCreator
from ..utils import ensure_uuid

# Configure logger
logger = logging.getLogger(__name__)

class SeedQuestionService:
    """
    Service for managing seed questions for trivia packs.
    Handles storage and retrieval of seed question data.
    """
    
    def __init__(self, pack_creation_data_repository: PackCreationDataRepository):
        """
        Initialize with required repositories.
        
        Args:
            pack_creation_data_repository: Repository for pack creation data operations
        """
        self.pack_creation_repository = pack_creation_data_repository
        # Fix: Initialize with llm_service=None instead of pack_creation_repository=None
        self.seed_processor = SeedQuestionProcessor(llm_service=None)
        # Add custom instructions creator
        self.custom_instructions_creator = CustomInstructionsCreator()
    
    async def store_seed_questions(self, pack_id: str, seed_questions: Dict[str, str]) -> bool:
        """
        Store seed questions in the pack_creation_data table.
        
        Args:
            pack_id: ID of the pack
            seed_questions: Dictionary of question-answer pairs
            
        Returns:
            Success flag
        """
        try:
            # Ensure pack_id is a valid UUID string
            pack_id = ensure_uuid(pack_id)
            
            # Check if there's already data for this pack
            existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
            
            if existing_data:
                # Update existing record
                update_data = PackCreationDataUpdate(
                    seed_questions=seed_questions
                )
                await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
                return True
            else:
                logger.warning(f"No existing pack creation data found for pack_id {pack_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing seed questions: {str(e)}")
            return False
    
    async def get_seed_questions(self, pack_id: str) -> Dict[str, str]:
        """
        Retrieve seed questions for a pack.
        
        Args:
            pack_id: ID of the pack
            
        Returns:
            Dictionary of seed questions
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'seed_questions'):
            return creation_data.seed_questions
        
        return {}
        
    async def store_custom_instructions(self, pack_id: str, custom_instructions: str) -> bool:
        """
        Store custom instructions in the pack_creation_data table.
        
        Args:
            pack_id: ID of the pack
            custom_instructions: Custom instructions for question generation
            
        Returns:
            Success flag
        """
        try:
            # Ensure pack_id is a valid UUID string
            pack_id = ensure_uuid(pack_id)
            
            # Check if there's already data for this pack
            existing_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
            
            if existing_data:
                # Update existing record
                update_data = PackCreationDataUpdate(
                    custom_question_instructions=custom_instructions
                )
                await self.pack_creation_repository.update(id=existing_data.id, obj_in=update_data)
                return True
            else:
                logger.warning(f"No existing pack creation data found for pack_id {pack_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing custom instructions: {str(e)}")
            return False
    
    async def get_custom_instructions(self, pack_id: str) -> Optional[str]:
        """
        Retrieve custom instructions for a pack.
        
        Args:
            pack_id: ID of the pack
            
        Returns:
            Custom instructions or None if not found
        """
        # Ensure pack_id is a valid UUID string
        pack_id = ensure_uuid(pack_id)
        
        creation_data = await self.pack_creation_repository.get_by_pack_id(pack_id)
        
        if creation_data and hasattr(creation_data, 'custom_question_instructions'):
            return creation_data.custom_question_instructions
        
        return None
    
    async def generate_custom_instructions(self, 
                                         pack_id: str, 
                                         pack_topic: str) -> Optional[str]:
        """
        Generate and store custom instructions based on seed questions and topic.
        
        Args:
            pack_id: ID of the pack
            pack_topic: Topic to base instructions on
            
        Returns:
            Generated custom instructions or None if generation failed
        """
        try:
            # Ensure pack_id is a valid UUID string
            pack_id = ensure_uuid(pack_id)
            
            # Get existing seed questions if available
            seed_questions = await self.get_seed_questions(pack_id)
            
            # Generate custom instructions
            custom_instructions = await self.custom_instructions_creator.generate_custom_instructions(
                pack_topic=pack_topic,
                seed_questions=seed_questions
            )
            
            # Store the generated instructions
            success = await self.store_custom_instructions(
                pack_id=pack_id,
                custom_instructions=custom_instructions
            )
            
            if success:
                return custom_instructions
            else:
                logger.warning(f"Failed to store generated custom instructions for pack_id {pack_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating custom instructions: {str(e)}")
            return None
    
    async def process_and_store_manual_instructions(self, 
                                                 pack_id: str, 
                                                 instructions: str) -> bool:
        """
        Process manually provided instructions and store them.
        
        Args:
            pack_id: ID of the pack
            instructions: Manually provided custom instructions
            
        Returns:
            Success flag
        """
        try:
            # Process the instructions
            processed_instructions = self.custom_instructions_creator.process_manual_instructions(instructions)
            
            # Store the processed instructions
            return await self.store_custom_instructions(
                pack_id=pack_id,
                custom_instructions=processed_instructions
            )
                
        except Exception as e:
            logger.error(f"Error processing manual custom instructions: {str(e)}")
            return False