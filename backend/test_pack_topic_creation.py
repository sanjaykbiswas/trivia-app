# backend/create_pack_topics.py
import asyncio
import uuid
import sys
import os
from pathlib import Path

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.repositories.pack_repository import PackRepository
from src.repositories.pack_creation_data_repository import PackCreationDataRepository
from src.utils.question_generation.pack_topic_creation import PackTopicCreation
from src.utils.llm.llm_service import LLMService
from src.models.pack import Pack, PackCreate, CreatorType


async def create_sample_pack_and_topics():
    """Create a sample pack and generate topics for it using LLM."""
    # Initialize Supabase client
    print("Initializing Supabase client...")
    supabase = await init_supabase_client()
    
    try:
        # Initialize repositories
        pack_repo = PackRepository(supabase)
        pack_creation_repo = PackCreationDataRepository(supabase)
        
        # Initialize LLM service
        llm_service = LLMService()
        
        # Initialize PackTopicCreation
        topic_creator = PackTopicCreation(
            pack_creation_data_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        # Create a sample pack
        pack_name = "Ancient Greece History"
        pack_description = "A fascinating journey through ancient Greek history, mythology, and culture."
        
        print(f"Creating pack: {pack_name}")
        pack_data = PackCreate(
            name=pack_name,
            description=pack_description,
            price=0.0,  # Free pack
            creator_type=CreatorType.SYSTEM,
        )
        
        new_pack = await pack_repo.create(obj_in=pack_data)
        print(f"Pack created with ID: {new_pack.id}")
        
        # Generate topics for the pack
        print("Generating topics with LLM...")
        topics = await topic_creator.create_pack_topics(
            creation_name=pack_name,
            creation_description=pack_description,
            num_topics=5
        )
        
        print("Generated topics:")
        for i, topic in enumerate(topics, 1):
            print(f"  {i}. {topic}")
        
        # Store the topics in the database
        print("Storing topics in database...")
        await topic_creator.store_pack_topics(
            pack_id=new_pack.id,
            topics=topics,
            creation_name=pack_name,
            creation_description=pack_description
        )
        
        print("Successfully created pack and topics!")
        
        # Return the created pack ID for reference
        return new_pack.id
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Close the Supabase client
        await close_supabase_client(supabase)
        print("Supabase client closed")


if __name__ == "__main__":
    print("Starting pack and topic creation...")
    pack_id = asyncio.run(create_sample_pack_and_topics())
    
    if pack_id:
        print(f"Process completed successfully. Pack ID: {pack_id}")
    else:
        print("Process failed.")
        sys.exit(1)