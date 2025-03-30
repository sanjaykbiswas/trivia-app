# backend/src/config/supabase_client.py (Updated Version)
from supabase import create_client, Client
import httpx
from .config import SupabaseConfig

async def init_supabase_client() -> Client:
    """
    Initialize an async Supabase client.
    
    Returns:
        An initialized Supabase client with async support
    """
    config = SupabaseConfig()
    
    # Create the Supabase client - simplified for compatibility
    supabase = create_client(
        config.get_supabase_url(),
        config.get_supabase_key()
    )
    
    return supabase

# Function to close the async client when done
async def close_supabase_client(client: Client):
    """
    Close the async HTTP client used by Supabase client.
    
    Args:
        client: The Supabase client to close
    """
    # Newer versions of the library manage their own client lifecycle
    # So this is now a no-op for compatibility
    pass