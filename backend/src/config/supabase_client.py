# backend/src/config/supabase_client.py
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
    
    # Create an httpx AsyncClient to enable async operations
    async_client = httpx.AsyncClient()
    
    # Create the Supabase client with async support
    supabase = create_client(
        config.get_supabase_url(),
        config.get_supabase_key(),
        options={
            "http_client": async_client,
            "auto_refresh_token": True,
            "persist_session": True
        }
    )
    
    return supabase

# Function to close the async client when done
async def close_supabase_client(client: Client):
    """
    Close the async HTTP client used by Supabase client.
    
    Args:
        client: The Supabase client to close
    """
    if hasattr(client, "http_client") and client.http_client:
        await client.http_client.aclose()