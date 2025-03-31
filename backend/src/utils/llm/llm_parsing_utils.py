# backend/src/utils/llm/llm_parsing_utils.py
"""
Utilities for parsing and processing outputs from LLM responses.

This module provides specialized functions to extract structured data
from LLM outputs and convert between various formats.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from ..document_processing.processors import clean_text, normalize_text

# Configure logger
logger = logging.getLogger(__name__)

class LLMParsingUtils:
    """
    Utilities for parsing and processing LLM outputs into structured formats.
    """
    
    @staticmethod
    def extract_bullet_list(text: str) -> List[str]:
        """
        Extract a bullet-pointed list from LLM text output.
        
        Args:
            text: Raw text containing bullet points
            
        Returns:
            List of extracted bullet point items
        """
        # Find all bullet points with various bullet characters
        bullet_pattern = r'(?:^|\n)\s*(?:•|\*|-|–|—|\d+\.)\s*(.+?)(?=$|\n)'
        matches = re.findall(bullet_pattern, text, re.MULTILINE)
        
        # Clean up each item
        items = []
        for match in matches:
            # Strip whitespace and remove any quotes
            cleaned = match.strip().strip('"\'')
            if cleaned:  # Only add non-empty items
                items.append(cleaned)
                
        return items
    
    @staticmethod
    def extract_numbered_list(text: str) -> List[Dict[str, Any]]:
        """
        Extract a numbered list with potential descriptions.
        
        Args:
            text: Raw text containing numbered items
            
        Returns:
            List of dictionaries with 'number' and 'content' keys
        """
        # Pattern to match numbered items: digit(s) + delimiter + content
        numbered_pattern = r'(?:^|\n)\s*(\d+)[.:\)]\s*(.+?)(?=$|\n)'
        matches = re.findall(numbered_pattern, text, re.MULTILINE)
        
        numbered_items = []
        for number, content in matches:
            cleaned_content = content.strip()
            if cleaned_content:
                numbered_items.append({
                    'number': int(number),
                    'content': cleaned_content
                })
        
        return numbered_items
    
    @staticmethod
    def extract_key_value_pairs(text: str, delimiter: str = ':') -> Dict[str, str]:
        """
        Extract key-value pairs from text.
        
        Args:
            text: Text containing key-value pairs
            delimiter: Character separating keys from values
            
        Returns:
            Dictionary of key-value pairs
        """
        pairs = {}
        
        # Split by lines and extract key-value pairs
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if delimiter in line:
                # Split on first occurrence of delimiter
                parts = line.split(delimiter, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Remove quotes if present
                    key = key.strip('"\'')
                    value = value.strip('"\'')
                    
                    if key:
                        pairs[key] = value
        
        return pairs
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> str:
        """
        Extract JSON content from a potentially mixed text response.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Cleaned JSON string
        """
        # Remove leading/trailing whitespace
        response_text = response_text.strip()
        
        # Check if the response is already valid JSON
        try:
            json.loads(response_text)
            return response_text
        except json.JSONDecodeError:
            pass  # Not valid JSON, continue with extraction
        
        # Try to extract JSON from markdown code blocks
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        code_blocks = re.findall(code_block_pattern, response_text)
        
        if code_blocks:
            # Try each extracted code block
            for block in code_blocks:
                try:
                    json.loads(block)
                    return block  # Return the first valid JSON block
                except json.JSONDecodeError:
                    continue  # Try next block if this one isn't valid
        
        # If no code blocks with valid JSON, look for array/object patterns
        # Find the first [ and last ]
        array_start = response_text.find("[")
        array_end = response_text.rfind("]")
        
        if array_start != -1 and array_end != -1 and array_start < array_end:
            potential_json = response_text[array_start:array_end+1]
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass  # Not valid JSON, continue with other methods
        
        # Find the first { and last }
        object_start = response_text.find("{")
        object_end = response_text.rfind("}")
        
        if object_start != -1 and object_end != -1 and object_start < object_end:
            potential_json = response_text[object_start:object_end+1]
            try:
                json.loads(potential_json)
                return potential_json
            except json.JSONDecodeError:
                pass  # Not valid JSON, continue with other methods
        
        # If all else fails, return the original text for further processing
        return response_text
    
    @staticmethod
    def parse_json_with_fallbacks(json_str: str, default_value: Any = None) -> Any:
        """
        Parse JSON with multiple fallback strategies.
        
        Args:
            json_str: JSON string to parse
            default_value: Default value to return if parsing fails
            
        Returns:
            Parsed JSON object or default value
        """
        # Try parsing directly first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass  # Move to fallback strategies
        
        # Extract JSON from mixed content
        cleaned_json = LLMParsingUtils.extract_json_from_response(json_str)
        
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            pass  # Move to next fallback
            
        # Handle potentially truncated arrays
        fixed_json = LLMParsingUtils.handle_truncated_json_array(cleaned_json)
        
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass  # Move to next fallback
        
        # Manual character-by-character cleanup
        sanitized_json = LLMParsingUtils.sanitize_json(fixed_json)
        
        try:
            return json.loads(sanitized_json)
        except json.JSONDecodeError:
            # Handle potentially truncated JSON array by recovering complete items
            if fixed_json.strip().startswith('['):
                # This looks like a JSON array, try to recover complete items
                recovered_items = LLMParsingUtils.recover_items_from_truncated_array(fixed_json)
                if recovered_items:
                    return recovered_items
            
            logger.error(f"Failed to parse JSON after all fallback attempts: {json_str[:100]}...")
            return default_value
    
    @staticmethod
    def handle_truncated_json_array(json_str: str) -> str:
        """
        Handles truncated JSON arrays by finding the last complete item.
        
        Args:
            json_str: Potentially truncated JSON string
            
        Returns:
            Fixed JSON string
        """
        # If it's already valid, return as is
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass  # Not valid JSON, try to fix
        
        # Check if it's an array format
        if not (json_str.strip().startswith('[') and ']' not in json_str or  # Completely missing closing bracket
               json_str.strip().startswith('[') and ']' in json_str):  # Has at least one closing bracket
            # Not an array, can't use this method
            return json_str
        
        try:
            # Find the last complete object by finding all complete items
            items = []
            depth = 0
            item_start = 1  # Skip initial '['
            in_string = False
            escape_char = False
            item_complete = False
            
            # For completely truncated arrays (no closing bracket)
            if ']' not in json_str:
                json_str = json_str + "]"  # Add a closing bracket for processing
            
            for i, char in enumerate(json_str[1:], 1):  # Skip initial '['
                # Handle string quotes and escaping
                if char == '"' and not escape_char:
                    in_string = not in_string
                elif char == '\\' and in_string and not escape_char:
                    escape_char = True
                    continue
                
                # Reset escape flag
                escape_char = False
                
                # Only count brackets when not inside a string
                if not in_string:
                    if char == '{' or char == '[':
                        depth += 1
                    elif char == '}' or char == ']':
                        depth -= 1
                        # If we just closed an object at the top level, mark it as complete
                        if depth == 0 and char == '}':
                            item_complete = True
                
                # Check if we have a complete item at the top level
                if depth == 0 and char == ',':
                    if item_complete:
                        item_end = i
                        items.append(json_str[item_start:item_end].strip())
                        item_start = i + 1
                        item_complete = False
                elif depth == -1 and char == ']':  # End of array
                    if item_complete:
                        item_end = i
                        if item_start < item_end:
                            # There's content before the closing bracket
                            items.append(json_str[item_start:item_end].strip())
                    break
            
            # If we found complete items, rebuild the array
            if items:
                return "[" + ",".join(items) + "]"
            
            # If we couldn't parse it this way, return original
            return json_str
            
        except Exception as e:
            logger.warning(f"Error handling truncated JSON: {e}")
            return json_str
    
    @staticmethod
    def recover_items_from_truncated_array(json_str: str) -> List[Any]:
        """
        Recover complete objects from a truncated JSON array by parsing each item separately.
        
        Args:
            json_str: Potentially truncated JSON array string
            
        Returns:
            List of successfully parsed items
        """
        # Regular expression to find potential complete JSON objects in the array
        # This captures each object between {} with proper nesting handling
        if not json_str.strip().startswith('['):
            return []
        
        recovered_items = []
        # Remove the opening bracket and any potential closing bracket
        content = json_str.strip()[1:]
        if content.endswith(']'):
            content = content[:-1]
            
        # Split by commas, but only at the top level
        depth = 0
        in_string = False
        escape_char = False
        current_item = ""
        
        for char in content:
            # Handle string quotes and escaping
            if char == '"' and not escape_char:
                in_string = not in_string
            elif char == '\\' and in_string:
                escape_char = True
                current_item += char
                continue
            else:
                escape_char = False
            
            # Track nested objects/arrays
            if not in_string:
                if char in '{[':
                    depth += 1
                elif char in '}]':
                    depth -= 1
            
            # If we're at top level and hit a comma, we have an item boundary
            if depth == 0 and char == ',' and not in_string:
                # Try to parse the current item
                try:
                    item_json = current_item.strip()
                    # Check if it looks like a complete item
                    if item_json.startswith('{') and item_json.endswith('}'):
                        item = json.loads(item_json)
                        recovered_items.append(item)
                except Exception:
                    # Skip invalid items
                    pass
                current_item = ""
            else:
                current_item += char
        
        # Check if there's a final item
        if current_item.strip():
            try:
                item_json = current_item.strip()
                if item_json.startswith('{') and item_json.endswith('}'):
                    item = json.loads(item_json)
                    recovered_items.append(item)
            except Exception:
                # Last item may be incomplete, skip it
                pass
        
        return recovered_items
    
    @staticmethod
    def sanitize_json(json_str: str) -> str:
        """
        Manually sanitize JSON string for common issues.
        
        Args:
            json_str: JSON string to sanitize
            
        Returns:
            Sanitized JSON string
        """
        # Replace common problematic patterns
        sanitized = json_str
        
        # Fix unescaped quotes in strings
        # This is a simplistic approach - full JSON parsing would be more robust
        sanitized = re.sub(r'(?<!\\)"([^"]*?)(?<!\\)"([^"]*?)(?<!\\)"', r'"\1\\"\2"', sanitized)
        
        # Fix trailing commas in arrays/objects
        sanitized = re.sub(r',\s*}', '}', sanitized)
        sanitized = re.sub(r',\s*\]', ']', sanitized)
        
        # Fix missing quotes around keys
        sanitized = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', sanitized)
        
        # Fix truncated arrays - if we have an opening [ but no closing ]
        if sanitized.strip().startswith('[') and ']' not in sanitized:
            sanitized = sanitized + ']'
        
        # Fix truncated objects - if we have an opening { but no closing }
        if sanitized.strip().startswith('{') and '}' not in sanitized:
            sanitized = sanitized + '}'
        
        return sanitized
    
    @staticmethod
    def detect_format(text: str) -> str:
        """
        Detect the format of the text from an LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Format type: 'json', 'bullet_list', 'numbered_list', 'key_value', or 'raw_text'
        """
        # Check for JSON format
        if (text.strip().startswith('{') and text.strip().endswith('}')) or \
           (text.strip().startswith('[') and text.strip().endswith(']')):
            try:
                json.loads(text.strip())
                return 'json'
            except json.JSONDecodeError:
                pass
        
        # Check for markdown code blocks containing JSON
        if '```json' in text or '```' in text:
            code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            code_blocks = re.findall(code_block_pattern, text)
            for block in code_blocks:
                try:
                    json.loads(block.strip())
                    return 'json'
                except json.JSONDecodeError:
                    continue
        
        # Check for bullet list
        bullet_pattern = r'(?:^|\n)\s*(?:•|\*|-|–|—)\s+.+'
        if re.search(bullet_pattern, text):
            return 'bullet_list'
        
        # Check for numbered list
        numbered_pattern = r'(?:^|\n)\s*\d+[.:\)]\s+.+'
        if re.search(numbered_pattern, text):
            return 'numbered_list'
        
        # Check for key-value pattern (at least 2 key-value pairs required)
        kv_pattern = r'(?:^|\n)\s*[A-Za-z0-9_\s]+\s*:\s*.+'
        kv_matches = re.findall(kv_pattern, text)
        if len(kv_matches) >= 2:
            return 'key_value'
        
        # Default to raw text
        return 'raw_text'
    
    @staticmethod
    def format_as_bullet_list(items: List[str]) -> str:
        """
        Format a list of items as a bullet list.
        
        Args:
            items: List of string items
            
        Returns:
            Formatted bullet list text
        """
        return "\n".join([f"- {item}" for item in items])
    
    @staticmethod
    def format_as_numbered_list(items: List[str]) -> str:
        """
        Format a list of items as a numbered list.
        
        Args:
            items: List of string items
            
        Returns:
            Formatted numbered list text
        """
        return "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    
    @staticmethod
    def format_as_key_value(data: Dict[str, Any]) -> str:
        """
        Format a dictionary as key-value pairs.
        
        Args:
            data: Dictionary to format
            
        Returns:
            Formatted key-value text
        """
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    @staticmethod
    def parse_based_on_format(text: str) -> Union[List, Dict, str]:
        """
        Parse text based on auto-detected format.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed data in appropriate structure
        """
        format_type = LLMParsingUtils.detect_format(text)
        
        if format_type == 'json':
            return LLMParsingUtils.parse_json_with_fallbacks(text, {})
        elif format_type == 'bullet_list':
            return LLMParsingUtils.extract_bullet_list(text)
        elif format_type == 'numbered_list':
            return LLMParsingUtils.extract_numbered_list(text)
        elif format_type == 'key_value':
            return LLMParsingUtils.extract_key_value_pairs(text)
        else:
            return clean_text(text)  # Default to cleaned text
    
    @staticmethod
    def extract_sections_by_headers(text: str) -> Dict[str, str]:
        """
        Extract sections from text based on headers.
        
        Args:
            text: Text with sections marked by headers
            
        Returns:
            Dictionary with header names as keys and content as values
        """
        # Look for patterns like "# Header" or "## Header" or "Header:" at the beginning of lines
        header_pattern = r'(?:^|\n)(?:#{1,3}\s+([^#\n]+)|([^:\n]+):)\s*\n'
        
        sections = {}
        header_positions = []
        
        # Find all headers and their positions
        for match in re.finditer(header_pattern, text, re.MULTILINE):
            header = match.group(1) or match.group(2)
            if header:
                header = header.strip()
                position = match.end()
                header_positions.append((header, position))
        
        # Extract content between headers
        for i, (header, start_pos) in enumerate(header_positions):
            # Find the end of this section (start of next section or end of text)
            end_pos = header_positions[i+1][1] if i < len(header_positions) - 1 else len(text)
            # Extract content
            content = text[start_pos:end_pos].strip()
            sections[header] = content
        
        return sections

# Helper functions for common parsing operations
def extract_bullet_list(text: str) -> List[str]:
    """Helper function to extract bullet list from text."""
    return LLMParsingUtils.extract_bullet_list(text)

def parse_json_from_llm(text: str, default_value: Any = None) -> Any:
    """Helper function to parse JSON from LLM output."""
    return LLMParsingUtils.parse_json_with_fallbacks(text, default_value)

def format_as_bullet_list(items: List[str]) -> str:
    """Helper function to format items as bullet list."""
    return LLMParsingUtils.format_as_bullet_list(items)

def extract_key_value_pairs(text: str) -> Dict[str, str]:
    """Helper function to extract key-value pairs from text."""
    return LLMParsingUtils.extract_key_value_pairs(text)

def detect_and_parse_format(text: str) -> Union[List, Dict, str]:
    """Helper function to detect and parse based on format."""
    return LLMParsingUtils.parse_based_on_format(text)