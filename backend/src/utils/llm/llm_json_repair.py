# backend/src/utils/llm/llm_json_repair.py
"""
Utility for repairing malformed JSON outputs from LLMs using LLM itself.

This module leverages LLMs to fix structural issues in JSON that
rule-based approaches might fail to address.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from .llm_service import LLMService
from ..document_processing.processors import clean_text

# Configure logger
logger = logging.getLogger(__name__)


class LLMJsonRepair:
    """
    Service for repairing malformed JSON using LLM capabilities.
    
    This class provides methods to fix common JSON issues by
    leveraging LLM's understanding of JSON structure.
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the JSON repair service.
        
        Args:
            llm_service: Service for LLM interactions. If None, creates a new instance.
        """
        self.llm_service = llm_service or LLMService()
    
    async def repair_json(self, malformed_json: str, json_type: str = "auto") -> str:
        """
        Repair malformed JSON using an LLM.
        
        Args:
            malformed_json: The malformed JSON string to repair
            json_type: Type of JSON structure expected ("object", "array", or "auto" for automatic detection)
            
        Returns:
            Repaired JSON string
        """
        # Detect JSON type if not specified
        if json_type == "auto":
            json_type = self._detect_json_type(malformed_json)
        
        # Create a prompt based on the JSON type
        prompt = self._create_repair_prompt(malformed_json, json_type)
        
        try:
            # Use LLM to generate a fixed version
            raw_response = await self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.2,  # Lower temperature for more deterministic output
                max_tokens=1500   # Ensure enough tokens for the repaired JSON
            )
            
            # Process and validate the response
            repaired_json = self._extract_json_from_response(raw_response)
            
            # Try to validate the result is proper JSON
            try:
                json.loads(repaired_json)
                logger.info("Successfully repaired JSON with LLM")
                return repaired_json
            except json.JSONDecodeError as e:
                logger.warning(f"LLM repair returned invalid JSON: {str(e)}")
                # Attempt second-level repair with more explicit instructions
                return await self._fallback_repair(repaired_json, json_type, str(e))
                
        except Exception as e:
            logger.error(f"Error repairing JSON with LLM: {str(e)}")
            # Return the original JSON if repair failed
            return malformed_json
    
    async def repair_and_parse(self, malformed_json: str, default_value: Any = None) -> Any:
        """
        Repair malformed JSON and parse it into a Python object.
        
        Args:
            malformed_json: The malformed JSON string to repair
            default_value: Default value to return if repair and parsing fails
            
        Returns:
            Parsed Python object (dict, list, etc.) or default_value if repair fails
        """
        # Try to parse directly first
        try:
            return json.loads(malformed_json)
        except json.JSONDecodeError:
            # If parsing fails, try to repair with LLM
            repaired_json = await self.repair_json(malformed_json)
            
            # Try to parse the repaired JSON
            try:
                return json.loads(repaired_json)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON even after LLM repair")
                return default_value
    
    def _detect_json_type(self, json_str: str) -> str:
        """
        Detect the type of JSON structure (object or array).
        
        Args:
            json_str: JSON string to analyze
            
        Returns:
            "object", "array", or "unknown"
        """
        # Clean and normalize the string
        cleaned = json_str.strip()
        
        # Check for array structure
        if cleaned.startswith('[') or re.search(r'\[\s*{', cleaned):
            return "array"
        # Check for object structure
        elif cleaned.startswith('{') or re.search(r'{\s*"', cleaned):
            return "object"
        # Check for items that look like they should be in an array
        elif re.search(r'{\s*".*":', cleaned) and ',' in cleaned:
            return "array"
        else:
            return "unknown"
    
    def _create_repair_prompt(self, malformed_json: str, json_type: str) -> str:
        """
        Create a prompt for the LLM to repair the JSON.
        
        Args:
            malformed_json: The malformed JSON string
            json_type: Type of JSON structure expected
            
        Returns:
            Formatted prompt for LLM
        """
        # Base prompt template
        base_prompt = f"""You are a JSON repair expert. I have a malformed or incomplete JSON that needs to be fixed.

The JSON is supposed to be a valid JSON {json_type}. Fix all structural issues, syntax errors, and incomplete elements.
Don't add or remove content unless necessary to make the JSON valid. Keep all existing data.

Here is the malformed JSON:
```
{malformed_json}
```

Please provide ONLY the corrected JSON with no explanation or markdown formatting. Don't use ```json or ``` tags.
"""
        
        # Add specific instructions based on JSON type
        if json_type == "array":
            base_prompt += "\nMake sure the output is a valid JSON array with properly formatted objects, valid commas, and balanced brackets."
        elif json_type == "object":
            base_prompt += "\nMake sure the output is a valid JSON object with proper key-value pairs, quotes around keys, valid commas, and balanced braces."
        
        return base_prompt
    
    async def _fallback_repair(self, json_str: str, json_type: str, error_message: str) -> str:
        """
        Fallback repair method with more explicit instructions about the error.
        
        Args:
            json_str: The JSON string that failed first repair attempt
            json_type: Type of JSON structure expected
            error_message: The error message from the JSON parser
            
        Returns:
            Repaired JSON string
        """
        # Create a more detailed prompt with specific error information
        prompt = f"""You are a JSON repair expert. The JSON I provided earlier is still invalid after one repair attempt.

The specific JSON error is: {error_message}

The JSON should be a valid {json_type}. Fix ONLY the structural issues causing this error.
Do not change any content unless absolutely necessary to make it valid JSON.

Here is the JSON to fix:
```
{json_str}
```

Return ONLY the fixed JSON with no explanation or markdown. Return it exactly as it should be parsed.
"""
        
        try:
            # Use LLM to generate a fixed version with lower temperature for precision
            raw_response = await self.llm_service.generate_content(
                prompt=prompt,
                temperature=0.1,
                max_tokens=1500
            )
            
            return self._extract_json_from_response(raw_response)
            
        except Exception as e:
            logger.error(f"Error in fallback JSON repair: {str(e)}")
            # Return the input JSON if fallback fails
            return json_str
    
    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response, handling potential markdown or explanation text.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Extracted JSON string
        """
        # Try to extract JSON from code blocks first
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        code_blocks = re.findall(code_block_pattern, response)
        
        if code_blocks:
            return code_blocks[0].strip()
        
        # If no code blocks, try to find JSON by brackets
        # For objects
        if '{' in response and '}' in response:
            object_start = response.find('{')
            object_end = response.rfind('}')
            if object_start < object_end:
                return response[object_start:object_end+1].strip()
        
        # For arrays
        if '[' in response and ']' in response:
            array_start = response.find('[')
            array_end = response.rfind(']')
            if array_start < array_end:
                return response[array_start:array_end+1].strip()
        
        # If no clear JSON structure is found, return the cleaned response
        return clean_text(response)


# Standalone helper functions for direct use
async def repair_json(malformed_json: str, json_type: str = "auto", llm_service: Optional[LLMService] = None) -> str:
    """
    Repair malformed JSON using an LLM.
    
    Args:
        malformed_json: The malformed JSON string to repair
        json_type: Type of JSON structure expected ("object", "array", or "auto")
        llm_service: Optional LLMService instance for LLM interaction
        
    Returns:
        Repaired JSON string
    """
    repair_service = LLMJsonRepair(llm_service)
    return await repair_service.repair_json(malformed_json, json_type)


async def repair_and_parse(malformed_json: str, default_value: Any = None, llm_service: Optional[LLMService] = None) -> Any:
    """
    Repair malformed JSON and parse it into a Python object.
    
    Args:
        malformed_json: The malformed JSON string to repair
        default_value: Default value to return if repair and parsing fails
        llm_service: Optional LLMService instance for LLM interaction
        
    Returns:
        Parsed Python object (dict, list, etc.) or default_value if repair fails
    """
    repair_service = LLMJsonRepair(llm_service)
    return await repair_service.repair_and_parse(malformed_json, default_value)