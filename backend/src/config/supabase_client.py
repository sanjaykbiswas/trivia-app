# backend/src/config/supabase_client.py
import logging
import traceback
from supabase import AsyncClient, acreate_client
from .config import SupabaseConfig

# Configure logger
logger = logging.getLogger(__name__)

async def init_supabase_client() -> AsyncClient:
    """
    Initialize an async Supabase client.
    
    Returns:
        An initialized asynchronous Supabase client
    """
    try:
        config = SupabaseConfig()
        logger.info(f"Initializing Supabase client with URL: {config.get_supabase_url()}")
        
        if not config.get_supabase_url() or not config.get_supabase_key():
            logger.error("Missing Supabase credentials in environment variables")
            raise ValueError("Supabase URL and key must be provided in environment variables")
        
        # Create the async Supabase client
        supabase = await acreate_client(
            config.get_supabase_url(),
            config.get_supabase_key()
        )
        
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def close_supabase_client(client: AsyncClient):
    """
    Close the async Supabase client when done.
    
    Args:
        client: The AsyncClient to close
    """
    try:
        if client and hasattr(client, 'session') and client.session:
            logger.info("Closing Supabase client session")
            await client.session.aclose()
            logger.info("Supabase client session closed")
    except Exception as e:
        logger.error(f"Error closing Supabase client: {str(e)}")
        logger.error(traceback.format_exc())