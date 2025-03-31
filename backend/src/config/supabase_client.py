# backend/src/config/supabase_client.py
from supabase import AsyncClient, acreate_client
from .config import SupabaseConfig

async def init_supabase_client() -> AsyncClient:
    """
    Initialize an async Supabase client.
    
    Returns:
        An initialized asynchronous Supabase client
    """
    config = SupabaseConfig()
    
    # Create the async Supabase client
    supabase = await acreate_client(
        config.get_supabase_url(),
        config.get_supabase_key()
    )
    
    return supabase

async def close_supabase_client(client: AsyncClient):
    """
    Close the async Supabase client when done.
    
    Args:
        client: The AsyncClient to close
    """
    if client and hasattr(client, 'session') and client.session:
        await client.session.aclose()