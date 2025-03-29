import os
from dotenv import load_dotenv

class Environment:
    """
    Centralized environment variable management
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Environment, cls).__new__(cls)
            load_dotenv()
            cls._instance._load_variables()
        return cls._instance
    
    def _load_variables(self):
        """Load all environment variables"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")  # Add this line
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai")  # Default to Openai
    
    def get(self, key, default=None):
        """Get an environment variable"""
        return getattr(self, key, default)