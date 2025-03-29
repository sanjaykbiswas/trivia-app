import anthropic
from openai import OpenAI
from config.environment import Environment

class LLMConfig:
    """
    Configuration for LLM clients
    """
    def __init__(self, provider=None, model=None):
        """
        Initialize LLM configuration with specified provider and model
        
        Args:
            provider (str, optional): LLM provider ('openai' or 'anthropic')
            model (str, optional): Specific model to use
        """
        env = Environment()
        self.provider = provider or env.get("llm_provider", "anthropic")
        self._initialize_client(model)
    
    def _initialize_client(self, model=None):
        """
        Initialize LLM client based on provider
        
        Args:
            model (str, optional): Specific model to override default
        """
        env = Environment()
        
        if self.provider == "openai":
            self.client = OpenAI(api_key=env.get("openai_api_key"))
            self.model = model or "gpt-4o"
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=env.get("anthropic_api_key"))
            self.model = model or "claude-3-7-sonnet-20250219"
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


class LLMConfigFactory:
    """
    Factory for creating LLMConfig instances with different configurations
    """
    @staticmethod
    def create(provider=None, model=None):
        """
        Create a new LLMConfig with specified provider and model
        
        Args:
            provider (str, optional): LLM provider ('openai' or 'anthropic')
            model (str, optional): Specific model to use
            
        Returns:
            LLMConfig: Configured LLM client
        """
        return LLMConfig(provider, model)
    
    @staticmethod
    def create_default():
        """
        Create LLMConfig with default settings from environment
        
        Returns:
            LLMConfig: Configured LLM client with default settings
        """
        return LLMConfig()
    
    @staticmethod
    def create_anthropic(model=None):
        """
        Create Anthropic-specific configuration
        
        Args:
            model (str, optional): Specific Anthropic model to use
            
        Returns:
            LLMConfig: Configured for Anthropic
        """
        return LLMConfig("anthropic", model)
    
    @staticmethod
    def create_openai(model=None):
        """
        Create OpenAI-specific configuration
        
        Args:
            model (str, optional): Specific OpenAI model to use
            
        Returns:
            LLMConfig: Configured for OpenAI
        """
        return LLMConfig("openai", model)