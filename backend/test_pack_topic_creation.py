# test_pack_topic_creation.py
import asyncio
import sys
import os
from pathlib import Path
import uuid

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.repositories.pack_repository import PackRepository
from src.repositories.pack_creation_data_repository import PackCreationDataRepository
from src.services.pack_service import PackService
from src.services.topic_service import TopicService
from src.models.pack import CreatorType

async def test_pack_topic_creation(
    pack_name: str, 
    num_topics: int = 5,
    debug_mode: bool = False
):
    """
    Test creating a pack with topics.
    
    Args:
        pack_name: Name of the pack to create
        num_topics: Number of topics to generate if creating a new pack
        debug_mode: Whether to show verbose debugging info
    """
    print("\n=== Testing Pack Creation with Topics ===\n")
    
    # Initialize Supabase client
    print("Initializing Supabase client...")
    supabase = await init_supabase_client()
    
    try:
        # Initialize repositories
        print("Creating repositories...")
        pack_repo = PackRepository(supabase)
        pack_creation_repo = PackCreationDataRepository(supabase)
        
        # Initialize services
        print("Initializing services...")
        pack_service = PackService(pack_repository=pack_repo)
        topic_service = TopicService(pack_creation_data_repository=pack_creation_repo)
        
        # Check if pack exists or create new pack
        print(f"\nGetting or creating pack: {pack_name}")
        pack, is_new = await pack_service.get_or_create_pack(
            pack_name=pack_name,
            price=0.0,
            creator_type=CreatorType.SYSTEM
        )
        
        if is_new:
            print(f"Created new pack with ID: {pack.id}")
        else:
            print(f"Retrieved existing pack with ID: {pack.id}")
        
        # Get existing topics or generate new ones
        existing_topics = await topic_service.get_existing_pack_topics(pack.id)
        
        if existing_topics:
            print("\nExisting topics:")
            for i, topic in enumerate(existing_topics, 1):
                print(f"  {i}. {topic}")
                
            # Ask if user wants to regenerate topics
            regenerate = input("\nDo you want to regenerate topics? (y/n) [n]: ").lower()
            if regenerate.startswith('y'):
                # Create new topics using TopicService
                print(f"\nGenerating {num_topics} new topics...")
                
                # Use the create_pack_topics method from the topic creator
                topics = await topic_service.topic_creator.create_pack_topics(
                    creation_name=pack_name,
                    num_topics=num_topics
                )
                
                print("\nGenerated topics:")
                for i, topic in enumerate(topics, 1):
                    print(f"  {i}. {topic}")
                
                # Store the topics
                print("\nStoring topics in database...")
                await topic_service.store_pack_topics(
                    pack_id=pack.id,
                    topics=topics,
                    creation_name=pack_name
                )
                
                # Update the existing_topics variable
                existing_topics = topics
        else:
            # No existing topics, generate new ones
            print(f"\nGenerating {num_topics} new topics...")
            
            # Use the create_pack_topics method from the topic creator
            topics = await topic_service.topic_creator.create_pack_topics(
                creation_name=pack_name,
                num_topics=num_topics
            )
            
            print("\nGenerated topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
            
            # Store the topics
            print("\nStoring topics in database...")
            await topic_service.store_pack_topics(
                pack_id=pack.id,
                topics=topics,
                creation_name=pack_name
            )
            
            # Update the existing_topics variable
            existing_topics = topics
        
        # Check if user wants to add additional topics
        add_more = input("\nDo you want to add additional topics? (y/n) [n]: ").lower()
        if add_more.startswith('y'):
            num_more = input("How many additional topics? [3]: ")
            try:
                num_additional = int(num_more) if num_more.strip() else 3
            except ValueError:
                print("Invalid number. Using default value of 3 additional topics.")
                num_additional = 3
            
            print(f"\nGenerating {num_additional} additional topics...")
            
            # Add additional topics
            all_topics = await topic_service.add_additional_topics(
                pack_id=pack.id,
                creation_name=pack_name,
                num_additional_topics=num_additional
            )
            
            print("\nUpdated topics list:")
            for i, topic in enumerate(all_topics, 1):
                print(f"  {i}. {topic}")
        
        print("\nSuccessfully processed pack and topics!")
        
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
    print("Starting pack and topic creation test...")
    
    # Interactive prompts with defaults
    default_name = "World Geography Trivia"
    
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
    
    # Debug mode option
    debug_mode = input("Enable debug mode to show detailed output? (y/n) [n]: ").lower()
    debug_mode_enabled = debug_mode.startswith('y')
    
    # Run the test function
    pack_id = asyncio.run(test_pack_topic_creation(
        pack_name, 
        num_topics,
        debug_mode_enabled
    ))
    
    if pack_id:
        print(f"\nProcess completed successfully. Pack ID: {pack_id}")
    else:
        print("\nProcess failed.")
        sys.exit(1)