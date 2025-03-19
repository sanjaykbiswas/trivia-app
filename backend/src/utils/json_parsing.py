import json
import re
import logging
from typing import List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

class JSONParsingUtils:
    """
    Enhanced utilities for robust JSON parsing from LLM responses
    """
    
    @staticmethod
    def extract_json_from_response(response_text: str) -> str:
        """
        Extract JSON content from a potentially mixed text response
        
        Args:
            response_text (str): Raw response from LLM
            
        Returns:
            str: Cleaned JSON string
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
    def handle_truncated_json_array(json_str: str) -> str:
        """
        Handles truncated JSON arrays by finding the last complete item
        
        Args:
            json_str (str): Potentially truncated JSON string
            
        Returns:
            str: Fixed JSON string
        """
        # If it's already valid, return as is
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass  # Not valid JSON, try to fix
        
        # Check if it's an array format
        if not (json_str.strip().startswith('[') and ']' in json_str):
            # Not an array, can't use this method
            return json_str
        
        try:
            # Find the last complete object by finding all complete items
            items = []
            depth = 0
            item_start = 1  # Skip initial '['
            in_string = False
            escape_char = False
            
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
                
                # Check if we have a complete item at the top level
                if depth == 0 and char == ',':
                    item_end = i
                    items.append(json_str[item_start:item_end].strip())
                    item_start = i + 1
                elif depth == -1 and char == ']':  # End of array
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
    def extract_questions_and_answers(text: str) -> List[Dict[str, Any]]:
        """
        Extract questions and answers from text by looking for patterns
        
        Args:
            text (str): Text containing questions and answers
            
        Returns:
            List[Dict]: List of question/answer dictionaries
        """
        results = []
        
        # Look for patterns like "Question: What...?" followed by "Correct Answer: ..." 
        # and "Incorrect Answer Array: [...]" or similar variations
        question_pattern = r'(?:"|\')?(?:Question|Question:|"Question"|\'Question\')\s*(?:"|\')?:\s*(?:"|\')?([^"\']+)(?:"|\')?'
        correct_answer_pattern = r'(?:"|\')?(?:Correct Answer|Correct Answer:|"Correct Answer"|\'Correct Answer\')\s*(?:"|\')?:\s*(?:"|\')?([^"\']+)(?:"|\')?'
        incorrect_answers_start = r'(?:"|\')?(?:Incorrect Answer Array|Incorrect Answer Array:|Incorrect Answers|Incorrect Answers:|"Incorrect Answer Array"|\'Incorrect Answer Array\'|"Incorrect Answers"|\'Incorrect Answers\')\s*(?:"|\')?:\s*(?:\[|\()'
        incorrect_answer_pattern = r'(?:"|\')?([^"\']+)(?:"|\')?'
        
        # Find all questions
        questions = re.findall(question_pattern, text)
        correct_answers = re.findall(correct_answer_pattern, text)
        
        # Find incorrect answers sections
        incorrect_sections = []
        for match in re.finditer(incorrect_answers_start, text):
            start_idx = match.end()
            # Find closing bracket
            depth = 1
            in_string = False
            end_idx = start_idx
            
            for i in range(start_idx, len(text)):
                if text[i] == '"' and (i == 0 or text[i-1] != '\\'):
                    in_string = not in_string
                
                if not in_string:
                    if text[i] in ('[', '('):
                        depth += 1
                    elif text[i] in (']', ')'):
                        depth -= 1
                        if depth == 0:
                            end_idx = i + 1
                            break
            
            if end_idx > start_idx:
                incorrect_section = text[start_idx:end_idx]
                incorrect_sections.append(incorrect_section)
        
        # Extract individual incorrect answers from each section
        all_incorrect_answers = []
        for section in incorrect_sections:
            # Clean the section
            section = section.strip('[]() \t\n\r,')
            section_answers = []
            
            # Handle comma-separated values
            items = []
            current_item = ""
            in_quotes = False
            
            for char in section:
                if char == '"' and (not current_item or current_item[-1] != '\\'):
                    in_quotes = not in_quotes
                    current_item += char
                elif char == ',' and not in_quotes:
                    items.append(current_item.strip())
                    current_item = ""
                else:
                    current_item += char
            
            if current_item:
                items.append(current_item.strip())
            
            # Clean up items
            for item in items:
                item = item.strip('"\'[] \t\n\r,')
                if item:
                    section_answers.append(item)
            
            if not section_answers and section:
                # Try simpler approach - just split by comma
                section_answers = [s.strip('"\'[] \t\n\r,') for s in section.split(',')]
                section_answers = [s for s in section_answers if s]
            
            if section_answers:
                all_incorrect_answers.append(section_answers)
        
        # Match everything together
        for i in range(min(len(questions), len(correct_answers), len(all_incorrect_answers))):
            results.append({
                "Question": questions[i],
                "Correct Answer": correct_answers[i],
                "Incorrect Answer Array": all_incorrect_answers[i]
            })
        
        return results
    
    @staticmethod
    def parse_json_with_fallbacks(json_str: str, default_value: Any = None) -> Any:
        """
        Parse JSON with multiple fallback strategies
        
        Args:
            json_str (str): JSON string to parse
            default_value (Any): Default value to return if parsing fails
            
        Returns:
            Any: Parsed JSON object or default value
        """
        # Try parsing directly first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass  # Move to fallback strategies
        
        # Extract JSON from mixed content
        cleaned_json = JSONParsingUtils.extract_json_from_response(json_str)
        
        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError:
            pass  # Move to next fallback
            
        # Handle potentially truncated arrays
        fixed_json = JSONParsingUtils.handle_truncated_json_array(cleaned_json)
        
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            pass  # Move to next fallback
        
        # Manual character-by-character cleanup
        sanitized_json = JSONParsingUtils.sanitize_json(fixed_json)
        
        try:
            return json.loads(sanitized_json)
        except json.JSONDecodeError:
            pass  # Move to next fallback
        
        # Last resort: try to extract questions and answers using regex
        if '[' in json_str and ']' in json_str:
            try:
                extracted_data = JSONParsingUtils.extract_questions_and_answers(json_str)
                if extracted_data:
                    logger.info(f"Successfully extracted {len(extracted_data)} Q&A pairs using regex")
                    return extracted_data
            except Exception as e:
                logger.warning(f"Error during regex extraction: {e}")
        
        # All fallbacks failed, return default
        logger.error(f"Failed to parse JSON after all fallback attempts: {json_str[:100]}...")
        return default_value
    
    @staticmethod
    def sanitize_json(json_str: str) -> str:
        """
        Manually sanitize JSON string for common issues
        
        Args:
            json_str (str): JSON string to sanitize
            
        Returns:
            str: Sanitized JSON string
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
        
        return sanitized
    
    @staticmethod
    def ensure_list_structure(json_data: Any) -> List:
        """
        Ensure the parsed JSON data is a list, even if it was nested under a key
        
        Args:
            json_data (Any): Parsed JSON data
            
        Returns:
            List: List representation of the data
        """
        if isinstance(json_data, list):
            return json_data
            
        # If it's a dict, check common keys that might contain the list
        if isinstance(json_data, dict):
            for key in ['questions', 'results', 'data', 'items', 'list', 'response', 'content']:
                if key in json_data and isinstance(json_data[key], list):
                    return json_data[key]
                    
            # If it's a single item dict with one value that's a list, return that
            if len(json_data) == 1 and isinstance(list(json_data.values())[0], list):
                return list(json_data.values())[0]
                
        # If all else fails, wrap in a list
        return [json_data] if json_data is not None else []
    
    @staticmethod
    def validate_question_format(questions: List) -> List[str]:
        """
        Validate and clean question list format
        
        Args:
            questions (List): List of questions (strings or dicts)
            
        Returns:
            List[str]: List of question strings
        """
        result = []
        
        for q in questions:
            if isinstance(q, str):
                # Already a string
                result.append(q)
            elif isinstance(q, dict):
                # Check for common fields that might contain the question
                for key in ['question', 'Question', 'content', 'text', 'value']:
                    if key in q and isinstance(q[key], str):
                        result.append(q[key])
                        break
            
        return result
    
    @staticmethod
    def validate_answer_format(answers: List) -> List[Dict]:
        """
        Validate and clean answer list format
        
        Args:
            answers (List): List of answer objects
            
        Returns:
            List[Dict]: List of standardized answer dictionaries
        """
        result = []
        
        for a in answers:
            if not isinstance(a, dict):
                continue
                
            # Map of possible field names to our standard names
            field_mappings = {
                'correct_answer': ['Correct Answer', 'Correct_Answer', 'correctAnswer', 'correct', 'answer'],
                'incorrect_answers': ['Incorrect Answer Array', 'Incorrect_Answer_Array', 'Incorrect Answers', 'Incorrect_Answers', 'incorrectAnswers', 'incorrect', 'distractors']
            }
            
            standardized = {}
            
            # Check for question field
            question_field = None
            for key in ['Question', 'question', 'text', 'content']:
                if key in a and isinstance(a[key], str):
                    question_field = a[key]
                    standardized['question'] = question_field
                    break
            
            # Check for correct answer
            for standard_key, possible_keys in field_mappings.items():
                for key in possible_keys:
                    if key in a:
                        standardized[standard_key] = a[key]
                        break
            
            # Ensure incorrect_answers is a list
            if 'incorrect_answers' in standardized and not isinstance(standardized['incorrect_answers'], list):
                if isinstance(standardized['incorrect_answers'], str):
                    # Try to convert a comma-separated string to a list
                    standardized['incorrect_answers'] = [item.strip() for item in standardized['incorrect_answers'].split(',')]
                else:
                    # Can't salvage, remove it
                    del standardized['incorrect_answers']
            
            # Only add if it has the minimum required fields
            if 'correct_answer' in standardized and 'incorrect_answers' in standardized:
                result.append(standardized)
                
        return result