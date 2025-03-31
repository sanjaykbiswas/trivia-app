# backend/test_pack_difficulty_creation.py
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
from src.utils.question_generation.pack_difficulty_creation import PackDifficultyCreation
from src.utils.llm.llm_service import LLMService
from src.models.pack import Pack, CreatorType
from src.utils.question_generation.pack_management import get_or_create_pack


async def create_sample_pack_with_topics_and_difficulties(
    pack_name, 
    pack_description, 
    num_topics=5, 
    update_existing_difficulties=False,
    debug_mode=False  # New parameter for verbose debugging
):
    """
    Create a sample pack with topics and custom difficulty descriptions.
    
    Args:
        pack_name: Name of the pack to create or retrieve
        pack_description: Description of the pack 
        num_topics: Number of topics to generate if creating a new pack
        update_existing_difficulties: Whether to update existing difficulty descriptions if found
        debug_mode: Whether to show verbose debugging info
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
        
        # Initialize creators
        topic_creator = PackTopicCreation(
            pack_creation_data_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        difficulty_creator = PackDifficultyCreation(
            pack_creation_data_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        print(f"Getting or creating pack: {pack_name}")
        
        # Use the get_or_create_pack utility
        pack, is_new = await get_or_create_pack(
            pack_repo=pack_repo,
            pack_name=pack_name,
            pack_description=pack_description,
            price=0.0,
            creator_type=CreatorType.SYSTEM
        )
        
        if is_new:
            print(f"Created new pack with ID: {pack.id}")
            
            # DEBUGGING: Capture raw topic generation response before parsing
            if debug_mode:
                print("\n--- DEBUGGING: Topic Generation ---")
                topic_prompt = topic_creator._build_topic_generation_prompt(
                    creation_name=pack_name,
                    creation_description=pack_description,
                    num_topics=num_topics
                )
                print("\nTopic Generation Prompt:")
                print(topic_prompt)
                
                raw_topic_response = await llm_service.generate_content(topic_prompt)
                processed_topic_response = await llm_service.process_llm_response(raw_topic_response)
                
                print("\nRaw Topic Response from LLM:")
                print(processed_topic_response)
            
            # Generate topics for the new pack
            print("\nGenerating topics with LLM...")
            topics = await topic_creator.create_pack_topics(
                creation_name=pack_name,
                creation_description=pack_description,
                num_topics=num_topics
            )
            
            print("\nParsed Topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
            
            # Store the topics in the database
            print("\nStoring topics in database...")
            await topic_creator.store_pack_topics(
                pack_id=pack.id,
                topics=topics,
                creation_name=pack_name,
                creation_description=pack_description
            )
            
            # DEBUGGING: Capture raw difficulty description generation response before parsing
            if debug_mode:
                print("\n--- DEBUGGING: Difficulty Description Generation ---")
                difficulty_prompt = difficulty_creator._build_difficulty_prompt(
                    creation_name=pack_name,
                    pack_topics=topics
                )
                print("\nDifficulty Generation Prompt:")
                print(difficulty_prompt)
                
                raw_diff_response = await llm_service.generate_content(difficulty_prompt)
                processed_diff_response = await llm_service.process_llm_response(raw_diff_response)
                
                print("\nRaw Difficulty Response from LLM:")
                print(processed_diff_response)
                
                print("\nParsed Difficulty Output:")
                difficulty_parsed = difficulty_creator._parse_difficulty_response(processed_diff_response)
                for level, desc in difficulty_parsed.items():
                    print(f"  {level}: {desc}")
            
            # Generate and store difficulty descriptions
            print("\nGenerating difficulty descriptions...")
            difficulty_descriptions = await difficulty_creator.generate_and_handle_existing_difficulty_descriptions(
                pack_id=pack.id,
                creation_name=pack_name,
                pack_topics=topics,
                force_regenerate=False
            )
            
            print("\nStored Difficulty Descriptions:")
            for desc in difficulty_descriptions:
                print(f"  {desc}")
            
            # Generate bullet format for LLM operations
            print("\nBullet format for LLM operations:")
            bullet_format = difficulty_creator.format_descriptions_for_prompt(difficulty_descriptions)
            print(bullet_format)
            
        else:
            print(f"Retrieved existing pack with ID: {pack.id}")
            
            # Get existing topics
            topics = await topic_creator.get_existing_pack_topics(pack.id)
            
            print("\nExisting topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
            
            # DEBUGGING: Show the raw response for difficulty descriptions even for existing packs
            if debug_mode and update_existing_difficulties:
                print("\n--- DEBUGGING: Difficulty Description Generation (Update) ---")
                difficulty_prompt = difficulty_creator._build_difficulty_prompt(
                    creation_name=pack_name,
                    pack_topics=topics
                )
                print("\nDifficulty Generation Prompt:")
                print(difficulty_prompt)
                
                raw_diff_response = await llm_service.generate_content(difficulty_prompt)
                processed_diff_response = await llm_service.process_llm_response(raw_diff_response)
                
                print("\nRaw Difficulty Response from LLM:")
                print(processed_diff_response)
                
                print("\nParsed Difficulty Output:")
                difficulty_parsed = difficulty_creator._parse_difficulty_response(processed_diff_response)
                for level, desc in difficulty_parsed.items():
                    print(f"  {level}: {desc}")
            
            # Generate and handle difficulty descriptions - use the existing method
            print("\nChecking and generating difficulty descriptions as needed...")
            difficulty_descriptions = await difficulty_creator.generate_and_handle_existing_difficulty_descriptions(
                pack_id=pack.id,
                creation_name=pack_name,
                pack_topics=topics,
                force_regenerate=update_existing_difficulties
            )
            
            print("\nDifficulty descriptions:")
            for desc in difficulty_descriptions:
                print(f"  {desc}")
            
            # Generate bullet format for LLM operations in both cases
            print("\nBullet format for LLM operations:")
            bullet_format = difficulty_creator.format_descriptions_for_prompt(difficulty_descriptions)
            print(bullet_format)
        
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


async def generate_specific_difficulty_levels(pack_id, difficulty_levels, debug_mode=False):
    """
    Update specific difficulty levels for an existing pack.
    
    Args:
        pack_id: UUID of the existing pack
        difficulty_levels: List of difficulty levels to update (e.g., ["Hard", "Expert"])
        debug_mode: Whether to show verbose debugging info
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
        
        # Initialize creators
        topic_creator = PackTopicCreation(
            pack_creation_data_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        difficulty_creator = PackDifficultyCreation(
            pack_creation_data_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        # Get the pack
        pack = await pack_repo.get_by_id(uuid.UUID(pack_id))
        if not pack:
            print(f"Pack with ID {pack_id} not found")
            return None
        
        print(f"Found pack: {pack.name}")
        
        # Get topics
        topics = await topic_creator.get_existing_pack_topics(pack.id)
        
        # DEBUGGING: Show the raw response for specific difficulty generation
        if debug_mode:
            print("\n--- DEBUGGING: Specific Difficulty Description Generation ---")
            # Generate all difficulty descriptions to see raw output
            all_desc_prompt = difficulty_creator._build_difficulty_prompt(
                creation_name=pack.name,
                pack_topics=topics
            )
            print("\nDifficulty Generation Prompt:")
            print(all_desc_prompt)
            
            raw_diff_response = await llm_service.generate_content(all_desc_prompt)
            processed_diff_response = await llm_service.process_llm_response(raw_diff_response)
            
            print("\nRaw Difficulty Response from LLM:")
            print(processed_diff_response)
            
            print("\nParsed Difficulty Output:")
            difficulty_parsed = difficulty_creator._parse_difficulty_response(processed_diff_response)
            for level, desc in difficulty_parsed.items():
                print(f"  {level}: {desc}")
        
        print(f"\nGenerating specific difficulty descriptions for levels: {', '.join(difficulty_levels)}")
        updated_descriptions = await difficulty_creator.generate_specific_difficulty_descriptions(
            pack_id=pack.id,
            creation_name=pack.name,
            pack_topics=topics,
            difficulty_levels=difficulty_levels
        )
        
        print("\nUpdated difficulty descriptions:")
        for desc in updated_descriptions:
            print(f"  {desc}")
        
        # Generate bullet format for LLM operations
        print("\nBullet format for specific difficulty levels:")
        bullet_format = difficulty_creator.format_descriptions_for_prompt(
            updated_descriptions, 
            difficulties=difficulty_levels
        )
        print(bullet_format)
        
        print("\nBullet format for all difficulty levels:")
        full_bullet_format = difficulty_creator.format_descriptions_for_prompt(updated_descriptions)
        print(full_bullet_format)
        
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
    print("Starting pack, topic, and difficulty creation test...")
    
    # Interactive prompts with defaults
    default_name = "Ancient Greece History"
    default_description = "A fascinating journey through ancient Greek history, mythology, and culture."
    
    # Ask for pack name
    pack_name = input(f"Enter pack name [{default_name}]: ")
    if not pack_name.strip():
        pack_name = default_name
    
    # Ask for pack description
    pack_description = input(f"Enter pack description [{default_description}]: ")
    if not pack_description.strip():
        pack_description = default_description
    
    # Ask for number of topics
    topics_input = input("Enter number of topics to generate [5]: ")
    try:
        num_topics = int(topics_input) if topics_input.strip() else 5
    except ValueError:
        print("Invalid number. Using default value of 5 topics.")
        num_topics = 5
    
    # Ask whether to update existing difficulty descriptions
    update_existing = input("Update existing difficulty descriptions if found? (y/n) [n]: ").lower()
    update_existing_difficulties = update_existing.startswith('y')
    
    # New option for debug mode
    debug_mode = input("Enable debug mode to show raw LLM responses? (y/n) [n]: ").lower()
    debug_mode_enabled = debug_mode.startswith('y')
    
    print(f"Update existing difficulties: {update_existing_difficulties}")
    print(f"Debug mode: {debug_mode_enabled}")
    
    # Run the main function
    pack_id = asyncio.run(create_sample_pack_with_topics_and_difficulties(
        pack_name, 
        pack_description,
        num_topics,
        update_existing_difficulties,
        debug_mode_enabled
    ))
    
    if pack_id:
        print(f"Process completed successfully. Pack ID: {pack_id}")
        
        # Ask if user wants to update specific difficulty levels
        update_specific = input("Do you want to update specific difficulty levels? (y/n) [n]: ").lower()
        if update_specific.startswith('y'):
            # Get difficulty levels to update
            difficulties_input = input("Enter difficulty levels to update (comma-separated, e.g., 'Hard,Expert'): ")
            difficulty_levels = [level.strip() for level in difficulties_input.split(',') if level.strip()]
            
            if difficulty_levels:
                print(f"Updating difficulty levels: {', '.join(difficulty_levels)}")
                asyncio.run(generate_specific_difficulty_levels(pack_id, difficulty_levels, debug_mode_enabled))
            else:
                print("No valid difficulty levels provided. Skipping specific update.")
    else:
        print("Process failed.")
        sys.exit(1)