# test_pack_with_difficulties.py
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
from src.services.difficulty_service import DifficultyService
from src.models.pack import CreatorType

async def test_pack_with_difficulties(
    pack_name: str, 
    pack_description: str,
    num_topics: int = 5,
    update_existing_difficulties: bool = False,
    debug_mode: bool = False
):
    """
    Test creating a pack with topics and custom difficulty descriptions.
    
    Args:
        pack_name: Name of the pack to create
        pack_description: Description of the pack
        num_topics: Number of topics to generate if creating a new pack
        update_existing_difficulties: Whether to update existing difficulty descriptions if found
        debug_mode: Whether to show verbose debugging info
    """
    print("\n=== Testing Pack Creation with Topics and Difficulty Descriptions ===\n")
    
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
        difficulty_service = DifficultyService(pack_creation_data_repository=pack_creation_repo)
        
        # Check if pack exists or create new pack
        print(f"\nGetting or creating pack: {pack_name}")
        pack, is_new = await pack_service.get_or_create_pack(
            pack_name=pack_name,
            pack_description=pack_description,
            price=0.0,
            creator_type=CreatorType.SYSTEM
        )
        
        if is_new:
            print(f"Created new pack with ID: {pack.id}")
            
            # Generate topics for the new pack
            print(f"\nGenerating {num_topics} topics...")
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
        else:
            print(f"Retrieved existing pack with ID: {pack.id}")
            
            # Get existing topics
            topics = await topic_service.get_existing_pack_topics(pack.id)
            
            print("\nExisting topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
                
            # Ask if user wants to regenerate topics
            regenerate = input("\nDo you want to regenerate topics? (y/n) [n]: ").lower()
            if regenerate.startswith('y'):
                print(f"\nRegenerating {num_topics} topics...")
                topics = await topic_service.topic_creator.create_pack_topics(
                    creation_name=pack_name,
                    num_topics=num_topics
                )
                
                print("\nNew topics:")
                for i, topic in enumerate(topics, 1):
                    print(f"  {i}. {topic}")
                
                # Store the new topics
                print("\nStoring topics in database...")
                await topic_service.store_pack_topics(
                    pack_id=pack.id,
                    topics=topics,
                    creation_name=pack_name
                )
        
        # Check for existing difficulty descriptions
        print("\nChecking for existing difficulty descriptions...")
        existing_difficulties = await difficulty_service.get_existing_difficulty_descriptions(pack.id)
        
        # Check if we have any custom descriptions
        has_custom_descriptions = False
        for level_data in existing_difficulties.values():
            if level_data.get("custom", ""):
                has_custom_descriptions = True
                break
        
        if has_custom_descriptions and not update_existing_difficulties:
            print("\nExisting difficulty descriptions found:")
            for level, data in existing_difficulties.items():
                custom_desc = data.get("custom", "")
                if custom_desc:
                    print(f"  {level}: {custom_desc}")
                    
            # Ask if user wants to update existing difficulty descriptions
            update = input("\nDo you want to update these difficulty descriptions? (y/n) [n]: ").lower()
            if update.startswith('y'):
                update_existing_difficulties = True
        
        # Generate or update difficulty descriptions
        if not has_custom_descriptions or update_existing_difficulties:
            print("\nGenerating difficulty descriptions...")
            
            if debug_mode:
                print("\nGenerating with debug info...")
                prompt = difficulty_service.difficulty_creator._build_difficulty_prompt(
                    creation_name=pack_name,
                    pack_topics=topics
                )
                print("\nDifficulty Generation Prompt:")
                print(prompt)
            
            # Generate and store difficulty descriptions
            difficulty_json = await difficulty_service.generate_and_store_difficulty_descriptions(
                pack_id=pack.id,
                creation_name=pack_name,
                pack_topics=topics
            )
            
            print("\nGenerated difficulty descriptions:")
            for level, data in difficulty_json.items():
                custom_desc = data.get("custom", "")
                print(f"  {level}: {custom_desc}")
            
            # Show bullet format for LLM usage
            print("\nBullet format for LLM operations:")
            bullet_format = difficulty_service.difficulty_creator.format_descriptions_for_prompt(difficulty_json)
            print(bullet_format)
        
        # Ask if user wants to update specific difficulty levels
        update_specific = input("\nDo you want to update specific difficulty levels? (y/n) [n]: ").lower()
        if update_specific.startswith('y'):
            difficulties_input = input("Enter difficulty levels to update (comma-separated, e.g., 'Hard,Expert'): ")
            difficulty_levels = [level.strip() for level in difficulties_input.split(',') if level.strip()]
            
            if difficulty_levels:
                print(f"\nGenerating specific difficulty descriptions for: {', '.join(difficulty_levels)}...")
                updated_difficulties = await difficulty_service.generate_specific_difficulty_descriptions(
                    pack_id=pack.id,
                    creation_name=pack_name,
                    pack_topics=topics,
                    difficulty_levels=difficulty_levels
                )
                
                print("\nUpdated difficulty descriptions:")
                for level in difficulty_levels:
                    if level in updated_difficulties:
                        custom_desc = updated_difficulties[level].get("custom", "")
                        print(f"  {level}: {custom_desc}")
                
                # Show bullet format for specific difficulty levels
                print("\nBullet format for specific levels:")
                specific_bullet_format = difficulty_service.difficulty_creator.format_descriptions_for_prompt(
                    updated_difficulties, 
                    difficulties=difficulty_levels
                )
                print(specific_bullet_format)
        
        print("\nSuccessfully processed pack, topics, and difficulty descriptions!")
        
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
    print("Starting pack creation with difficulty descriptions test...")
    
    # Interactive prompts with defaults
    default_name = "Ancient History Trivia"
    default_description = "A collection of trivia questions about ancient civilizations"
    
    # Ask for pack name
    pack_name = input(f"Enter pack name [{default_name}]: ")
    if not pack_name.strip():
        pack_name = default_name
    
    # Ask for pack description
    pack_desc = input(f"Enter pack description [{default_description}]: ")
    if not pack_desc.strip():
        pack_desc = default_description
    
    # Ask for number of topics
    topics_input = input("Enter number of topics to generate [5]: ")
    try:
        num_topics = int(topics_input) if topics_input.strip() else 5
    except ValueError:
        print("Invalid number. Using default value of 5 topics.")
        num_topics = 5
    
    # Ask whether to update existing difficulty descriptions
    update_existing = input("Force update existing difficulty descriptions? (y/n) [n]: ").lower()
    update_existing_difficulties = update_existing.startswith('y')
    
    # Debug mode option
    debug_mode = input("Enable debug mode to show prompts and responses? (y/n) [n]: ").lower()
    debug_mode_enabled = debug_mode.startswith('y')
    
    # Run the test function
    pack_id = asyncio.run(test_pack_with_difficulties(
        pack_name, 
        pack_desc,
        num_topics,
        update_existing_difficulties,
        debug_mode_enabled
    ))
    
    if pack_id:
        print(f"\nProcess completed successfully. Pack ID: {pack_id}")
    else:
        print("\nProcess failed.")
        sys.exit(1)