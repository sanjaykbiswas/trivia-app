# test_supabase_async.py
import asyncio
import sys
import os
from pathlib import Path

# Add backend/src to the Python path
current_dir = Path(os.getcwd())
sys.path.insert(0, str(current_dir))

from src.config.config import SupabaseConfig
from src.config.supabase_client import init_supabase_client, close_supabase_client
from src.repositories.user_repository import UserRepository
from src.repositories.pack_repository import PackRepository

async def test_async_repositories():
    """Test async repository operations with Supabase."""
    print("\n=== Testing Async Repository Operations ===\n")
    
    # Initialize Supabase client
    print("Initializing Supabase client...")
    supabase = await init_supabase_client()
    
    try:
        # Initialize repositories
        print("Creating repositories...")
        user_repo = UserRepository(supabase)
        pack_repo = PackRepository(supabase)
        
        # Test User Repository
        print("\n--- Testing User Repository ---")
        users = await user_repo.get_all(limit=5)
        print(f"Retrieved {len(users)} users")
        
        # Test Pack Repository
        print("\n--- Testing Pack Repository ---")
        packs = await pack_repo.get_all(limit=5)
        print(f"Retrieved {len(packs)} packs")
        
        print("\nAsync repository tests completed successfully!")
        
    except Exception as e:
        print(f"Error during repository operations: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the Supabase client
        await close_supabase_client(supabase)
        print("Supabase client closed")

if __name__ == "__main__":
    print("Starting async Supabase repository tests...")
    # Get Supabase config to verify environment variables are loaded
    config = SupabaseConfig()
    print(f"Supabase URL configured: {'Yes' if config.get_supabase_url() else 'No'}")
    print(f"Supabase Key configured: {'Yes' if config.get_supabase_key() else 'No'}")
    
    # Run the async test
    asyncio.run(test_async_repositories())