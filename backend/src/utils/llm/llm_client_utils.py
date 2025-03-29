import logging
import json
import asyncio
from typing import Any, Dict, Union, Optional, List, Callable

from config.llm_config import LLMConfigFactory

# Configure logger
logger = logging.getLogger(__name__)

class LLMClientUtils:
    """
    Utility class for centralized LLM client operations
    
    This class provides standardized methods for LLM prompting, response handling,
    and error management to ensure consistent behavior across all LLM interactions.
    """
    
    def __init__(self, llm_config=None):
        """
        Initialize with optional LLM configuration
        
        Args:
            llm_config: LLM configuration object (defaults to environment config)
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        
        # Create response parser functions map
        self._response_parsers = {
            "json": self._parse_json_response,
            "text": self._parse_text_response,
            "structured": self._parse_structured_response
        }
        
        # Cache for prompt responses
        self._response_cache = {}
        
    async def generate_text_async(self, prompt: str, response_type: str = "text", cache_key: str = None) -> Any:
        """
        Generate text from LLM asynchronously
        
        Args:
            prompt (str): Prompt text to send to LLM
            response_type (str): Type of response to parse ('text', 'json', 'structured')
            cache_key (str, optional): Key for caching the response
            
        Returns:
            Any: Parsed response based on response_type
        """
        # Check cache if key provided
        if cache_key and cache_key in self._response_cache:
            logger.info(f"Using cached response for key: {cache_key}")
            return self._response_cache[cache_key]
        
        # Generate response in thread pool to avoid blocking
        raw_response = await asyncio.to_thread(
            self._call_llm,
            prompt
        )
        
        # Parse response based on type
        parser = self._response_parsers.get(response_type, self._parse_text_response)
        parsed_response = parser(raw_response)
        
        # Cache if key provided
        if cache_key:
            self._response_cache[cache_key] = parsed_response
            
        return parsed_response
    
    def generate_text(self, prompt: str, response_type: str = "text", cache_key: str = None) -> Any:
        """
        Generate text from LLM (synchronous wrapper)
        
        Args:
            prompt (str): Prompt text to send to LLM
            response_type (str): Type of response to parse ('text', 'json', 'structured')
            cache_key (str, optional): Key for caching the response
            
        Returns:
            Any: Parsed response based on response_type
        """
        # Check cache if key provided
        if cache_key and cache_key in self._response_cache:
            logger.info(f"Using cached response for key: {cache_key}")
            return self._response_cache[cache_key]
        
        # Call LLM directly
        raw_response = self._call_llm(prompt)
        
        # Parse response based on type
        parser = self._response_parsers.get(response_type, self._parse_text_response)
        parsed_response = parser(raw_response)
        
        # Cache if key provided
        if cache_key:
            self._response_cache[cache_key] = parsed_response
            
        return parsed_response
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM client with prompt
        
        Args:
            prompt (str): Prompt text
            
        Returns:
            str: Raw LLM response
        """
        try:
            logger.info(f"Calling {self.provider} model {self.model}")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if response.choices:
                    logger.info(f"Received response from {self.provider}")
                    return response.choices[0].message.content
                return ""  # Empty string if no response
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if isinstance(response.content, list) and len(response.content) > 0:
                    logger.info(f"Received response from {self.provider}")
                    return response.content[0].text
                return ""  # Empty string if no response
                
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return ""  # Empty string on error
    
    def _parse_json_response(self, raw_response: str) -> Any:
        """
        Parse JSON response from LLM
        
        Args:
            raw_response (str): Raw LLM response
            
        Returns:
            Any: Parsed JSON object or empty list/dict on error
        """
        if not raw_response:
            return []
            
        try:
            # Check if it's already a Python object
            if isinstance(raw_response, (dict, list)):
                return raw_response
                
            # Try to parse as JSON
            return json.loads(raw_response)
            
        except json.JSONDecodeError:
            # Try to extract JSON from response
            try:
                from utils.json_parsing import JSONParsingUtils
                return JSONParsingUtils.parse_json_with_fallbacks(raw_response, default_value=[])
            except ImportError:
                # Basic fallback if JSONParsingUtils not available
                logger.warning("JSONParsingUtils not available, using basic extraction")
                return self._basic_json_extraction(raw_response)
    
    def _basic_json_extraction(self, text: str) -> Any:
        """
        Basic JSON extraction from text when JSONParsingUtils is not available
        
        Args:
            text (str): Text containing JSON
            
        Returns:
            Any: Extracted JSON or empty list
        """
        # Find JSON array or object
        start_idx = max(text.find("["), text.find("{"))
        end_idx = max(text.rfind("]"), text.rfind("}"))
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            try:
                return json.loads(text[start_idx:end_idx+1])
            except json.JSONDecodeError:
                pass
                
        return []  # Return empty list as fallback
    
    def _parse_text_response(self, raw_response: str) -> str:
        """
        Parse text response from LLM
        
        Args:
            raw_response (str): Raw LLM response
            
        Returns:
            str: Cleaned text response
        """
        if isinstance(raw_response, str):
            return raw_response.strip()
        return str(raw_response)
    
    def _parse_structured_response(self, raw_response: str) -> Dict:
        """
        Parse structured response (key-value pairs) from LLM
        
        Args:
            raw_response (str): Raw LLM response
            
        Returns:
            Dict: Structured response as dictionary
        """
        # First try JSON parsing
        json_result = self._parse_json_response(raw_response)
        if isinstance(json_result, dict):
            return json_result
            
        # If not a dictionary, try basic line-by-line parsing
        result = {}
        if isinstance(raw_response, str):
            lines = raw_response.strip().split("\n")
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    result[key.strip()] = value.strip()
                    
        return result
    
    def clear_cache(self):
        """Clear the response cache"""
        self._response_cache = {}
        
    def invalidate_cache_key(self, key: str):
        """
        Invalidate a specific cache key
        
        Args:
            key (str): Cache key to invalidate
        """
        if key in self._response_cache:
            del self._response_cache[key]