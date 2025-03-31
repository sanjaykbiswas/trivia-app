# backend/src/utils/llm/llm_service.py
from typing import Optional, Dict, Any
from ...config.config import LLMConfig
from ..document_processing.processors import clean_text, normalize_text

class LLMService:
    """
    Service for interacting with Language Model APIs.
    Abstracts the details of different LLM providers.
    """
    
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """
        Initialize the LLM service with configuration.
        
        Args:
            llm_config: Configuration for LLM providers. If None, uses default config.
        """
        self.llm_config = llm_config or LLMConfig()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
    
    async def generate_content(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, 
                              clean_prompt: bool = False) -> str:
        """
        Generate content using the configured LLM provider.
        
        Args:
            prompt: The prompt to send to the LLM
            temperature: Controls randomness (0-1), higher = more random
            max_tokens: Maximum number of tokens to generate
            clean_prompt: Whether to clean and normalize the prompt text
            
        Returns:
            String containing the raw LLM response
        """
        # Clean prompt if requested - using utility from document_processing
        if clean_prompt:
            prompt = clean_text(prompt, remove_extra_whitespace=True)
        
        # Call appropriate method based on provider
        if self.provider == "openai":
            return await self._generate_with_openai(prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            return await self._generate_with_anthropic(prompt, temperature, max_tokens)
        elif self.provider == "gemini":
            return await self._generate_with_gemini(prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_with_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate content using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates high-quality trivia content."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    async def _generate_with_anthropic(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate content using Anthropic API."""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="You are a helpful assistant that creates high-quality trivia content.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    async def _generate_with_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate content using Google's Gemini API."""
        genai = self.client
        model = genai.GenerativeModel(self.model)
        response = await model.generate_content_async(  # Changed to async version
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        return response.text
    
    async def process_llm_response(self, response: str, normalize: bool = True, 
                                 remove_extra_whitespace: bool = True) -> str:
        """
        Process an LLM response using document processing utilities.
        
        Args:
            response: Raw LLM response text
            normalize: Whether to normalize the text
            remove_extra_whitespace: Whether to remove extra whitespace
            
        Returns:
            Processed response text
        """
        # Clean the text first
        processed_text = clean_text(response, remove_extra_whitespace=remove_extra_whitespace)
        
        # Normalize if requested
        if normalize:
            processed_text = normalize_text(processed_text, lowercase=False)
            
        return processed_text