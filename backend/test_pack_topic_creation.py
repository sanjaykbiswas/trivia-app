# backend/test_pack_topic_creation.py
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
from src.models.pack import Pack, CreatorType
from src.utils.question_generation.pack_management import get_or_create_pack


async def create_sample_pack_and_topics(pack_name, num_topics=5):
    """
    Create a sample pack and generate topics for it using LLM.
    
    Args:
        pack_name: Name of the pack to create or retrieve
        num_topics: Number of topics to generate if creating a new pack
    """
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
        
        print(f"Getting or creating pack: {pack_name}")
        
        # Use the get_or_create_pack utility
        pack, is_new = await get_or_create_pack(
            pack_repo=pack_repo,
            pack_name=pack_name,
            pack_description=pack_name,  # Use name as description
            price=0.0,
            creator_type=CreatorType.SYSTEM
        )
        
        if is_new:
            print(f"Created new pack with ID: {pack.id}")
            
            # Generate topics for the new pack
            print("Generating topics with LLM...")
            topics = await topic_creator.create_pack_topics(
                creation_name=pack_name,
                num_topics=num_topics
            )
            
            print("Generated topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
            
            # Store the topics in the database
            print("Storing topics in database...")
            await topic_creator.store_pack_topics(
                pack_id=pack.id,
                topics=topics,
                creation_name=pack_name
            )
        else:
            print(f"Retrieved existing pack with ID: {pack.id}")
            
            # Get existing topics
            topics = await topic_creator.get_existing_pack_topics(pack.id)
            
            print("Existing topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
        
        print("Successfully processed pack and topics!")
        
        # Return the pack ID for reference
        return pack.id
        
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
    
    # Interactive prompts with defaults
    default_name = "Ancient Greece History"
    
    # Ask for pack name
    pack_name = input(f"Enter pack name [{default_name}]: ")
    if not pack_name.strip():
        pack_name = default_name
    
    # Ask for number of topics
    topics_input = input("Enter number of topics to generate [5]: ")
    try:
        num_topics = int(topics_input) if topics_input.strip() else 5
    except ValueError:
        print("Invalid number. Using default value of 5 topics.")
        num_topics = 5
    
    pack_id = asyncio.run(create_sample_pack_and_topics(
        pack_name, 
        num_topics
    ))
    
    if pack_id:
        print(f"Process completed successfully. Pack ID: {pack_id}")
    else:
        print("Process failed.")
        sys.exit(1)