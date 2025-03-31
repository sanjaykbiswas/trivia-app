# backend/test_seed_question_processor.py
import asyncio
import sys
import os
from pathlib import Path

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.repositories.pack_repository import PackRepository
from src.repositories.pack_creation_data_repository import PackCreationDataRepository
from src.utils.question_generation.seed_question_processor import SeedQuestionProcessor
from src.utils.llm.llm_service import LLMService
from src.models.pack import Pack, CreatorType
from src.utils.question_generation.pack_management import get_or_create_pack
from src.utils import ensure_uuid


async def process_and_store_seed_questions(pack_id, input_content, input_type=None):
    """
    Process seed questions from input content and store them in Supabase.
    
    Args:
        pack_id: UUID of the pack
        input_content: CSV or text content with questions and answers
        input_type: Optional type hint ('csv' or 'text')
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
        
        # Initialize seed question processor
        processor = SeedQuestionProcessor(
            pack_creation_repository=pack_creation_repo,
            llm_service=llm_service
        )
        
        # Retrieve the pack
        pack = await pack_repo.get_by_id(ensure_uuid(pack_id))
        
        if not pack:
            print(f"Pack with ID {pack_id} not found")
            return
        
        print(f"Processing seed questions for pack: {pack.name}")
        
        # Process the input based on specified type or auto-detect
        if input_type == 'csv':
            seed_questions = await processor.process_csv_content(input_content)
        elif input_type == 'text':
            seed_questions = await processor.process_text_content(input_content)
        else:
            # Auto-detect and process
            seed_questions = await processor.detect_and_process_input(input_content)
        
        print(f"\nExtracted {len(seed_questions)} question-answer pairs:")
        for i, (question, answer) in enumerate(seed_questions.items(), 1):
            if i <= 5:  # Print only first 5 for readability
                print(f"{i}. Q: {question}")
                print(f"   A: {answer}")
        
        if len(seed_questions) > 5:
            print(f"... and {len(seed_questions) - 5} more pairs")
        
        # Store the seed questions
        if seed_questions:
            print("\nStoring seed questions in database...")
            success = await processor.store_seed_questions(pack.id, seed_questions)
            
            if success:
                print("Seed questions stored successfully!")
            else:
                print("Failed to store seed questions.")
        else:
            print("\nNo valid question-answer pairs were extracted.")
        
        return seed_questions
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Close the Supabase client
        await close_supabase_client(supabase)
        print("Supabase client closed")


async def create_pack_and_process_seed_questions(pack_name, input_content, input_type=None):
    """
    Create a new pack and process seed questions for it.
    
    Args:
        pack_name: Name of the pack to create
        input_content: CSV or text content with questions and answers
        input_type: Optional type hint ('csv' or 'text')
    """
    # Initialize Supabase client
    print("Initializing Supabase client...")
    supabase = await init_supabase_client()
    
    try:
        # Initialize repositories
        pack_repo = PackRepository(supabase)
        
        print(f"Creating or retrieving pack: {pack_name}")
        
        # Create or get the pack
        pack, is_new = await get_or_create_pack(
            pack_repo=pack_repo,
            pack_name=pack_name,
            pack_description=f"Trivia pack about {pack_name}",
            price=0.0,
            creator_type=CreatorType.SYSTEM
        )
        
        if is_new:
            print(f"Created new pack with ID: {pack.id}")
        else:
            print(f"Retrieved existing pack with ID: {pack.id}")
        
        # Now process and store the seed questions
        await process_and_store_seed_questions(pack.id, input_content, input_type)
        
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
    # You can either specify a pack ID or create a new pack
    use_existing_pack = input("Do you want to use an existing pack? (y/n) [n]: ").lower()
    
    if use_existing_pack.startswith('y'):
        # Use existing pack
        pack_id_input = input("Enter pack ID: ")
        
        # Check if input content is a file path or raw text
        file_path = input("Enter file path (or leave empty to input text directly): ")
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Try to determine file type from extension
            input_type = None
            if file_path.lower().endswith('.csv'):
                input_type = 'csv'
            else:
                input_type = 'text'
                
            print(f"Detected file type: {input_type}")
        else:
            print("Enter text content (end with a blank line):")
            content_lines = []
            while True:
                line = input()
                if not line:
                    break
                content_lines.append(line)
            
            content = "\n".join(content_lines)
            input_type = 'text'
        
        asyncio.run(process_and_store_seed_questions(pack_id_input, content, input_type))
    else:
        # Create new pack
        pack_name = input("Enter new pack name: ")
        
        # Check if input content is a file path or raw text
        file_path = input("Enter file path (or leave empty to input text directly): ")
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Try to determine file type from extension
            input_type = None
            if file_path.lower().endswith('.csv'):
                input_type = 'csv'
            else:
                input_type = 'text'
                
            print(f"Detected file type: {input_type}")
        else:
            print("Enter text content (end with a blank line):")
            content_lines = []
            while True:
                line = input()
                if not line:
                    break
                content_lines.append(line)
            
            content = "\n".join(content_lines)
            input_type = 'text'
        
        asyncio.run(create_pack_and_process_seed_questions(pack_name, content, input_type))