# backend/src/utils/question_generator/difficulty_helper.py
import json
import re
import logging
from config.llm_config import LLMConfigFactory
from utils.json_parsing import JSONParsingUtils

# Configure logger
logger = logging.getLogger(__name__)

class DifficultyHelper:
    """
    Generates difficulty-specific guidelines for question generation
    """
    def __init__(self, llm_config=None):
        """
        Initialize the difficulty helper    
        Args:
            llm_config (LLMConfig, optional): Specific LLM configuration to use
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        
        # Five standard difficulty levels
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
        
        # Add a cache for difficulty guidelines
        self._difficulty_cache = {}
    
    def generate_difficulty_guidelines(self, category, category_guidelines=None):
        """
        Generate guidelines for defining the difficulty of questions in a specific category
        
        Args:
            category (str): The category to generate difficulty guidelines for
            category_guidelines (str, optional): Category guidelines to provide context
            
        Returns:
            dict: Structured difficulty guidelines with keys for each tier
        """
        # Check cache first
        category_key = category.lower().strip()
        if category_key in self._difficulty_cache:
            logger.info(f"Using cached difficulty guidelines for '{category}'")
            return self._difficulty_cache[category_key]
        
        # If no category_guidelines provided, use a placeholder
        if not category_guidelines:
            category_guidelines = f"Guidelines for the category '{category}'."
            
        prompt = f"""
        ## Create 5 distinct difficulty tiers for the category: '{category}'
        - Develop the 5 tiers based on a progression of difficulties that span beginner to expert-level knowledge
        - The difficulty order should Easy, Medium, Hard, Expert, and Master 

        ## Use the following category guidelines for additional context:
        {category_guidelines}
        
        ## Consider the following progression axes:
        - Knowledge progression (casual → specialized → expert)
        - Skill level (basic recall → complex analysis)
        - Audience familiarity (general public → dedicated enthusiasts → professionals)
        - Depth of subject matter (common facts → obscure details)
        - Breadth across knowledge domains within '{category}'
        - Number of contextual cues within question language (more = easier, fewer = harder, none = hardest)

        ## Format your response as JSON, following this exact structure:

        {{
            "Easy": "2-3 sentence description of knowledge level, question types, and target audience",
            "Medium": "2-3 sentence description of knowledge level, question types, and target audience",
            "Hard": "2-3 sentence description of knowledge level, question types, and target audience",
            "Expert": "2-3 sentence description of knowledge level, question types, and target audience",
            "Master": "2-3 sentence description of knowledge level, question types, and target audience"
        }}

        ## Ensure you include all 5 tiers exactly as named above and provide detailed, unique descriptions for each level.
        """
        
        try:
            logger.info(f"Calling {self.provider} model {self.model} for difficulty guidelines")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if response.choices:
                    logger.info(f"Received response from {self.provider}")
                    raw_response = response.choices[0].message.content
                else:
                    logger.warning("No choices in OpenAI response")
                    result = self._get_default_difficulties(category)
                    self._difficulty_cache[category_key] = result
                    return result
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if isinstance(response.content, list) and len(response.content) > 0:
                    logger.info(f"Received response from {self.provider}")
                    raw_response = response.content[0].text
                else:
                    logger.warning("No content in Anthropic response")
                    result = self._get_default_difficulties(category)
                    self._difficulty_cache[category_key] = result
                    return result
            
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Check if raw_response is already a dictionary
            if isinstance(raw_response, dict):
                logger.info("Response is already a dictionary, no parsing needed")
                result = self._validate_difficulty_levels(raw_response, category)
                self._difficulty_cache[category_key] = result
                return result
                
            # Parse the response into a structured format using the utility
            try:
                parsed_data = JSONParsingUtils.parse_json_with_fallbacks(
                    raw_response, 
                    default_value={}
                )
                
                result = self._validate_difficulty_levels(parsed_data, category)
                self._difficulty_cache[category_key] = result
                return result
                
            except Exception as e:
                logger.error(f"Error parsing difficulty response: {e}")
                result = self._get_default_difficulties(category)
                self._difficulty_cache[category_key] = result
                return result
                
        except Exception as e:
            logger.error(f"Error generating difficulty guidelines: {e}")
            result = self._get_default_difficulties(category)
            # Don't cache error responses
            return result
    
    def _validate_difficulty_levels(self, parsed_data, category):
        """
        Validate that all required difficulty levels are present
        
        Args:
            parsed_data (dict): Parsed difficulty data
            category (str): Category name for default values
            
        Returns:
            dict: Validated difficulty guidelines
        """
        # Ensure all difficulty levels are present
        result = {}
        for level in self.difficulty_levels:
            if level in parsed_data:
                result[level] = parsed_data[level]
            else:
                logger.warning(f"Missing difficulty level: {level}")
                result[level] = f"Default {level.lower()} difficulty for {category}."
                
        return result
    
    def _get_default_difficulties(self, category):
        """
        Generate default difficulty tiers if parsing fails
        
        Args:
            category (str): Category name
            
        Returns:
            dict: Default difficulty guidelines
        """
        return {
            "Easy": f"Basic knowledge of {category} suitable for beginners. Questions focus on common facts and well-known information that most people with casual interest would know.",
            "Medium": f"Intermediate knowledge of {category} for hobbyists. Questions require some specific knowledge and may cover less commonly known facts or events.",
            "Hard": f"Advanced knowledge of {category} for enthusiasts. Questions involve detailed information, connections between concepts, and some obscure facts.",
            "Expert": f"Specialized knowledge of {category} for professionals or serious enthusiasts. Questions require deep understanding of complex topics and obscure details.",
            "Master": f"Comprehensive mastery of {category} at an academic level. Questions demand exceptional knowledge, including obscure facts, technical details, and cutting-edge developments."
        }
    
    def get_difficulty_by_tier(self, difficulty_guidelines, tier):
        """
        Get difficulty description for a specific tier
        
        Args:
            difficulty_guidelines (dict): Structured difficulty guidelines
            tier (int or str): Tier number (1-5) or name (Easy, Medium, etc.)
            
        Returns:
            str: Difficulty description for the specified tier
        """
        if isinstance(tier, int) and 1 <= tier <= 5:
            level = self.difficulty_levels[tier-1]
            return difficulty_guidelines.get(level, "")
        
        if isinstance(tier, str) and tier in self.difficulty_levels:
            return difficulty_guidelines.get(tier, "")
        
        return ""