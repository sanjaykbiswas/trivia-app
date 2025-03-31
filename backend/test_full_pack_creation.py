# test_full_pack_creation.py
import asyncio
import sys
import os
from pathlib import Path
import json
import traceback
from typing import Any, Optional, Dict, List, Callable
import functools

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.repositories.pack_repository import PackRepository
from src.repositories.pack_creation_data_repository import PackCreationDataRepository
from src.repositories.question_repository import QuestionRepository
from src.repositories.incorrect_answers_repository import IncorrectAnswersRepository
from src.services.pack_service import PackService
from src.services.topic_service import TopicService
from src.services.difficulty_service import DifficultyService
from src.services.question_service import QuestionService
from src.utils.llm.llm_service import LLMService
from src.utils.llm.llm_parsing_utils import parse_json_from_llm
from src.utils.llm.llm_json_repair import repair_json, repair_and_parse
from src.models.pack import CreatorType
from src.models.question import DifficultyLevel

# Patch LLMService to print raw responses (CHANGED: removed async)
original_generate_content = LLMService.generate_content

def patched_generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, 
                          clean_prompt: bool = False) -> str:
    """Patched version of generate_content that prints the raw response"""
    # Call the original synchronous method (CHANGED: removed await)
    response = original_generate_content(self, prompt, temperature, max_tokens, clean_prompt)
    
    print("\n=== Raw LLM Response ===")
    print(response[:1000] + "..." if len(response) > 1000 else response)
    print("========================\n")
    
    return response

# Patch the method
LLMService.generate_content = patched_generate_content

# Patch parse_json_from_llm to detect when repair is used
original_parse_json_from_llm = parse_json_from_llm

async def patched_parse_json_from_llm(text: str, default_value: Any = None) -> Any:
    """Patched version that detects when LLM repair is invoked"""
    try:
        # Try direct JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # This is expected, continue with other methods
            pass
        
        # Try other parsing methods...
        # If we reach the LLM repair part, print a notification
        print("\n=== INVOKING LLM JSON REPAIR ===")
        print("Traditional JSON parsing failed, attempting repair with LLM")
        print("=====================================\n")
        
        # Call the original function's LLM repair part
        result = await original_parse_json_from_llm(text, default_value)
        
        # Check if repair was successful
        if result is not default_value:
            print("\n=== LLM JSON REPAIR SUCCEEDED ===")
            print("Successfully repaired and parsed JSON with LLM")
            print("==================================\n")
        else:
            print("\n=== LLM JSON REPAIR FAILED ===")
            print("Failed to repair JSON with LLM")
            print("==============================\n")
            
        return result
        
    except Exception as e:
        print(f"\n=== ERROR IN JSON PARSING ===")
        print(f"Error: {str(e)}")
        traceback.print_exc()
        print("============================\n")
        return default_value

# Apply the patch selectively when needed
def with_json_repair_monitoring(func):
    """Decorator to add JSON repair monitoring to a function"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Save the original
        original = sys.modules['src.utils.llm.llm_parsing_utils'].parse_json_from_llm
        # Apply the patch
        sys.modules['src.utils.llm.llm_parsing_utils'].parse_json_from_llm = patched_parse_json_from_llm
        try:
            # Call the function
            return await func(*args, **kwargs)
        finally:
            # Restore the original
            sys.modules['src.utils.llm.llm_parsing_utils'].parse_json_from_llm = original
    return wrapper

async def test_full_pack_creation(
    pack_name: str, 
    num_topics: int = 5,
    num_questions: int = 5,
    debug_mode: bool = False
):
    """
    Test creating a complete pack with topics, difficulty descriptions, and questions.
    
    Args:
        pack_name: Name of the pack to create
        num_topics: Number of topics to generate if creating a new pack
        num_questions: Number of questions to generate per topic/difficulty
        debug_mode: Whether to show verbose debugging info
    """
    print("\n=== Testing Full Pack Creation (Topics, Difficulties, Questions) ===\n")
    
    # Initialize Supabase client
    print("Initializing Supabase client...")
    supabase = await init_supabase_client()
    
    try:
        # Initialize repositories
        print("Creating repositories...")
        pack_repo = PackRepository(supabase)
        pack_creation_repo = PackCreationDataRepository(supabase)
        question_repo = QuestionRepository(supabase)
        incorrect_answers_repo = IncorrectAnswersRepository(supabase)
        
        # Initialize services
        print("Initializing services...")
        pack_service = PackService(pack_repository=pack_repo)
        topic_service = TopicService(pack_creation_data_repository=pack_creation_repo)
        difficulty_service = DifficultyService(pack_creation_data_repository=pack_creation_repo)
        question_service = QuestionService(
            question_repository=question_repo, 
            pack_creation_data_repository=pack_creation_repo
        )
        
        #=====================================================================
        # STEP 1: Create or get the pack
        #=====================================================================
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
            
        #=====================================================================
        # STEP 2: Generate or retrieve topics
        #=====================================================================
        existing_topics = await topic_service.get_existing_pack_topics(pack.id)
        
        if existing_topics:
            print("\nExisting topics:")
            for i, topic in enumerate(existing_topics, 1):
                print(f"  {i}. {topic}")
                
            regenerate = input("\nDo you want to regenerate topics? (y/n) [n]: ").lower()
            if regenerate.startswith('y'):
                print(f"\nRegenerating {num_topics} topics...")
                
                # Apply the monitoring decorator
                create_pack_topics = with_json_repair_monitoring(topic_service.topic_creator.create_pack_topics)
                topics = await create_pack_topics(
                    creation_name=pack_name,
                    num_topics=num_topics
                )
                
                print("\nNew topics:")
                for i, topic in enumerate(topics, 1):
                    print(f"  {i}. {topic}")
                
                await topic_service.store_pack_topics(
                    pack_id=pack.id,
                    topics=topics,
                    creation_name=pack_name
                )
            else:
                topics = existing_topics
        else:
            print(f"\nGenerating {num_topics} topics...")
            
            # Apply the monitoring decorator
            create_pack_topics = with_json_repair_monitoring(topic_service.topic_creator.create_pack_topics)
            topics = await create_pack_topics(
                creation_name=pack_name,
                num_topics=num_topics
            )
            
            print("\nGenerated topics:")
            for i, topic in enumerate(topics, 1):
                print(f"  {i}. {topic}")
            
            await topic_service.store_pack_topics(
                pack_id=pack.id,
                topics=topics,
                creation_name=pack_name
            )
            
        #=====================================================================
        # STEP 3: Generate or retrieve difficulty descriptions
        #=====================================================================
        print("\nChecking for existing difficulty descriptions...")
        existing_difficulties = await difficulty_service.get_existing_difficulty_descriptions(pack.id)
        
        # Check if we have any custom descriptions
        has_custom_descriptions = False
        for level_data in existing_difficulties.values():
            if level_data.get("custom", ""):
                has_custom_descriptions = True
                break
        
        if has_custom_descriptions:
            print("\nExisting difficulty descriptions found")
            
            # Print the descriptions if in debug mode
            if debug_mode:
                print("\nCurrent difficulty descriptions:")
                for level, data in existing_difficulties.items():
                    custom_desc = data.get("custom", "")
                    if custom_desc:
                        print(f"  {level}: {custom_desc[:100]}..." if len(custom_desc) > 100 else f"  {level}: {custom_desc}")
            
            regenerate_diff = input("Do you want to regenerate difficulty descriptions? (y/n) [n]: ").lower()
            if regenerate_diff.startswith('y'):
                print("\nRegenerating difficulty descriptions...")
                
                # Apply the monitoring decorator
                generate_and_store = with_json_repair_monitoring(difficulty_service.generate_and_store_difficulty_descriptions)
                difficulty_json = await generate_and_store(
                    pack_id=pack.id,
                    creation_name=pack_name,
                    pack_topics=topics
                )
            else:
                difficulty_json = existing_difficulties
        else:
            print("\nGenerating difficulty descriptions...")
            
            # Apply the monitoring decorator
            generate_and_store = with_json_repair_monitoring(difficulty_service.generate_and_store_difficulty_descriptions)
            difficulty_json = await generate_and_store(
                pack_id=pack.id,
                creation_name=pack_name,
                pack_topics=topics
            )
            
        print("\nDifficulty descriptions:")
        for level, data in difficulty_json.items():
            custom_desc = data.get("custom", "")
            if custom_desc:
                print(f"  {level}: {custom_desc[:100]}..." if len(custom_desc) > 100 else f"  {level}: {custom_desc}")
        
        #=====================================================================
        # STEP 4: Generate questions for a selected topic and difficulty
        #=====================================================================
        print("\n=== Question Generation ===")
        
        # Display topics for selection
        print("\nAvailable topics:")
        for i, topic in enumerate(topics, 1):
            print(f"  {i}. {topic}")
            
        # Let user select a topic
        topic_idx = 0
        while topic_idx < 1 or topic_idx > len(topics):
            try:
                topic_input = input(f"\nSelect a topic (1-{len(topics)}): ")
                topic_idx = int(topic_input)
                if topic_idx < 1 or topic_idx > len(topics):
                    print(f"Please enter a number between 1 and {len(topics)}")
            except ValueError:
                print("Please enter a valid number")
        
        selected_topic = topics[topic_idx - 1]
        print(f"\nSelected topic: {selected_topic}")
        
        # Let user select a difficulty level
        print("\nAvailable difficulty levels:")
        difficulty_levels = ["Easy", "Medium", "Hard", "Expert"]
        for i, level in enumerate(difficulty_levels, 1):
            print(f"  {i}. {level}")
            
        diff_idx = 0
        while diff_idx < 1 or diff_idx > len(difficulty_levels):
            try:
                diff_input = input(f"\nSelect a difficulty level (1-{len(difficulty_levels)}): ")
                diff_idx = int(diff_input)
                if diff_idx < 1 or diff_idx > len(difficulty_levels):
                    print(f"Please enter a number between 1 and {len(difficulty_levels)}")
            except ValueError:
                print("Please enter a valid number")
        
        selected_difficulty = difficulty_levels[diff_idx - 1]
        print(f"\nSelected difficulty: {selected_difficulty}")
        
        # Get the difficulty as a DifficultyLevel enum
        difficulty_enum = DifficultyLevel(selected_difficulty.lower())
        
        # Check if there are existing questions for this topic and difficulty
        existing_questions = await question_repo.get_by_pack_id(pack.id)
        matching_questions = [q for q in existing_questions 
                              if q.pack_topics_item == selected_topic 
                              and q.difficulty_current == difficulty_enum]
        
        if matching_questions:
            print(f"\nFound {len(matching_questions)} existing questions for this topic and difficulty:")
            for i, q in enumerate(matching_questions[:3], 1):  # Show at most 3 examples
                print(f"  {i}. Q: {q.question}")
                print(f"     A: {q.answer}")
                
            if len(matching_questions) > 3:
                print(f"  ... and {len(matching_questions) - 3} more")
                
            regenerate_questions = input("\nDo you want to generate new questions? (y/n) [n]: ").lower()
            if not regenerate_questions.startswith('y'):
                print("\nSkipping question generation")
                return pack.id
        
        # Generate new questions
        print(f"\nGenerating {num_questions} questions for '{selected_topic}' at {selected_difficulty} difficulty...")
        
        if debug_mode:
            # Get the formatted difficulty descriptions for the prompt
            difficulty_desc = difficulty_service.difficulty_creator.format_descriptions_for_prompt(
                difficulty_json, difficulties=[selected_difficulty]
            )
            print(f"\nUsing difficulty description:\n{difficulty_desc}")
        
        # Apply the monitoring decorator for question generation
        generate_and_store_questions = with_json_repair_monitoring(question_service.generate_and_store_questions)
        
        # Generate and store the questions
        generated_questions = await generate_and_store_questions(
            pack_id=pack.id,
            creation_name=pack_name,
            pack_topic=selected_topic,
            difficulty=difficulty_enum,
            num_questions=num_questions,
            debug_mode=debug_mode  # Pass debug mode to question service
        )
        
        # Display the generated questions
        if generated_questions:
            print(f"\nGenerated {len(generated_questions)} questions:")
            for i, q in enumerate(generated_questions, 1):
                print(f"  {i}. Q: {q.question}")
                print(f"     A: {q.answer}")
        else:
            print("\nNo questions were generated. Please check logs for errors.")
            
            # In debug mode, try to access the last raw response from the question generator
            if debug_mode and hasattr(question_service.question_generator, 'last_raw_response'):
                last_response = question_service.question_generator.last_raw_response
                if last_response:
                    print("\n=== Last Raw LLM Response (from debug data) ===")
                    print(last_response)
                    print("=================================================")
                    
                # Print the last processed questions if available
                if hasattr(question_service.question_generator, 'last_processed_questions'):
                    last_processed = question_service.question_generator.last_processed_questions
                    if last_processed:
                        print("\n=== Last Processed Questions (from debug data) ===")
                        try:
                            print(json.dumps(last_processed, indent=2))
                        except Exception as e:
                            print(f"Error displaying processed questions: {str(e)}")
                            print(f"Raw processed questions: {last_processed}")
                        print("====================================================")
        
        print("\nSuccessfully completed full pack creation process!")
        
        # Return the pack ID for reference
        return pack.id
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return None
    
    finally:
        # Restore original functions to avoid side effects
        LLMService.generate_content = original_generate_content
        
        # Close the Supabase client
        await close_supabase_client(supabase)
        print("Supabase client closed")

if __name__ == "__main__":
    print("Starting full pack creation test (topics, difficulties, questions)...")
    
    # Interactive prompts with defaults
    default_name = "Science Fiction Movies"
    
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
    
    # Ask for number of questions
    questions_input = input("Enter number of questions to generate per topic/difficulty [5]: ")
    try:
        num_questions = int(questions_input) if questions_input.strip() else 5
    except ValueError:
        print("Invalid number. Using default value of 5 questions.")
        num_questions = 5
    
    # Debug mode option
    debug_mode = input("Enable debug mode to show detailed information? (y/n) [n]: ").lower()
    debug_mode_enabled = debug_mode.startswith('y')
    
    # Run the test function
    pack_id = asyncio.run(test_full_pack_creation(
        pack_name, 
        num_topics,
        num_questions,
        debug_mode_enabled
    ))
    
    if pack_id:
        print(f"\nProcess completed successfully. Pack ID: {pack_id}")
    else:
        print("\nProcess failed.")
        sys.exit(1)