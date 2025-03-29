import os
from dotenv import load_dotenv
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

class LLMConfig:
    """
    Configuration for LLM clients (OpenAI, Anthropic, Gemini).
    """

    def __init__(self, provider=None, model=None):
        load_dotenv()
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self._initialize_client(model)

    def _initialize_client(self, model=None):
        if self.provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not found.")
            self.client = OpenAI(api_key=self.openai_api_key)
            self.model = model or "gpt-4o"
        elif self.provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not found.")
            self.client = Anthropic(api_key=self.anthropic_api_key)
            self.model = model or "claude-3-7-sonnet-20250219"
        elif self.provider == "gemini":
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found.")
            genai.configure(api_key=self.gemini_api_key)
            self.client = genai
            self.model = model or "gemini-1.5-pro-latest"
        else:
            raise ValueError(f"Invalid LLM provider: {self.provider}")

    def get_client(self):
        return self.client

    def get_model(self):
        return self.model

    def get_provider(self):
        return self.provider

    def get_api_key(self):
        if self.provider == "openai":
            return self.openai_api_key
        elif self.provider == "anthropic":
            return self.anthropic_api_key
        elif self.provider == "gemini":
            return self.gemini_api_key
        else:
            return None

    @staticmethod
    def create(provider=None, model=None):
        return LLMConfig(provider, model)


class SupabaseConfig:
    """
    Configuration for Supabase.
    """
    def __init__(self):
        load_dotenv()
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        if not self.supabase_url or not self.supabase_key or not self.supabase_jwt_secret:
             print("Warning: Some Supabase configuration values are missing from environment variables.") # Don't raise an error, as supabase may not always be needed

    def get_supabase_url(self):
        return self.supabase_url

    def get_supabase_key(self):
        return self.supabase_key

    def get_supabase_jwt_secret(self):
        return self.supabase_jwt_secret


# Example Usage
if __name__ == "__main__":
    # LLM Configurations
    default_config = LLMConfig()
    print(f"Default Provider: {default_config.get_provider()}")
    print(f"Default Model: {default_config.get_model()}")

    anthropic_config = LLMConfig(provider="anthropic", model="claude-3-opus-20240229")
    print(f"Anthropic Provider: {anthropic_config.get_provider()}")
    print(f"Anthropic Model: {anthropic_config.get_model()}")

    gemini_config = LLMConfig(provider="gemini", model="gemini-1.5-pro-latest")
    print(f"Gemini Provider: {gemini_config.get_provider()}")
    print(f"Gemini Model: {gemini_config.get_model()}")

    openai_config = LLMConfig.create(provider="openai", model="gpt-4o")
    print(f"OpenAI factory Provider: {openai_config.get_provider()}")
    print(f"OpenAI factory Model: {openai_config.get_model()}")


    # Supabase Configuration
    supabase_config = SupabaseConfig()
    print(f"Supabase URL: {supabase_config.get_supabase_url()}")  # These might print None if not set
    print(f"Supabase Key: {supabase_config.get_supabase_key()}")
    #print(f"Supabase JWT Secret: {supabase_config.get_supabase_jwt_secret()}") # Avoid printing secrets directly.