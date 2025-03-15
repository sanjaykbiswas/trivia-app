import anthropic
from openai import OpenAI
from config.environment import Environment

class LLMConfig:
    """
    Configuration for LLM clients
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMConfig, cls).__new__(cls)
            cls._instance._initialize_clients()
        return cls._instance
    
    def _initialize_clients(self):
        """Initialize LLM clients based on environment settings"""
        env = Environment()
        self.provider = env.get("llm_provider", "anthropic")
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=env.get("openai_api_key"))
            self.model = "gpt-4o"
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=env.get("anthropic_api_key"))
            self.model = "claude-3-7-sonnet-20250219"
        else:
            raise ValueError(f"Invalid LLM provider: {self.provider}")
    
    def get_client(self):
        """Get the configured LLM client"""
        return self.client
    
    def get_model(self):
        """Get the configured model name"""
        return self.model
    
    def get_provider(self):
        """Get the configured provider name"""
        return self.provider