import logging
from config.llm_config import LLMConfigFactory

# Configure logger
logger = logging.getLogger(__name__)

class CategoryHelper:
    """
    Generates category-specific guidelines for question generation
    """
    def __init__(self, llm_config=None):
        """
        Initialize the category helper
        
        Args:
            llm_config (LLMConfig, optional): Specific LLM configuration to use
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        
        # Add a cache for guidelines
        self._guidelines_cache = {}
    
    def generate_category_guidelines(self, category):
        """
        Generate guidelines for creating questions in a specific category
        
        Args:
            category (str): The category to generate guidelines for
            
        Returns:
            str: Guidelines text
        """
        # Check cache first
        category_key = category.lower().strip()
        if category_key in self._guidelines_cache:
            logger.info(f"Using cached category guidelines for '{category}'")
            return self._guidelines_cache[category_key]
            
        # Generate new guidelines
        prompt = f"""
        ## Create a comprehensive guide for generating exceptional trivia questions in the category: '{category}' by answering the following questions:
        - Is there a play on words in '{category}'?  
        - If there is a play on words, describe it.  If not, ignore this question.
        - What are the distinctive elements of '{category}'?
        - What are the key knowledge domains within '{category}'?
        - What are elements within '{category}' that could make the questions fun or interesting?
        
        Format your response using the structure below:

        ### Is '{category}' a play on words?
        - Yes or No
        - If Yes: Description of the play on words.  If No: do not include this line.
        - If Yes: "Include the nuances of the play on words in your question generation."
        
        ### Key Knowledge Domains (maximum 10)
        - Domain 1
        - ...
        - Domain N
        
        ### Fun, interesting, or distinctive elements (maximum 10)
        - Element 1
        - ...
        - Element N

        DO NOT INCLUDE ANY guidelines about the following: Visual Questions, Difficulty Balancing, Question Formats, Question Clarity, or Hypothetical Scenarios.
        """
        
        try:
            logger.info(f"Calling {self.provider} model {self.model} for category guidelines")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if response.choices:
                    logger.info(f"Received response from {self.provider}")
                    # Check if the response is already a string
                    content = response.choices[0].message.content
                    if isinstance(content, str):
                        # Cache the result before returning
                        self._guidelines_cache[category_key] = content
                        return content
                    else:
                        # Try to convert to string if it's not already
                        logger.warning(f"Unexpected response type: {type(content)}. Converting to string.")
                        content_str = str(content)
                        # Cache the result before returning
                        self._guidelines_cache[category_key] = content_str
                        return content_str
                else:
                    logger.warning("No choices in OpenAI response")
                    return "No guidelines available"
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                
                if isinstance(response.content, list) and len(response.content) > 0:
                    logger.info(f"Received response from {self.provider}")
                    content = response.content[0].text
                    if isinstance(content, str):
                        # Cache the result before returning
                        self._guidelines_cache[category_key] = content
                        return content
                    else:
                        # Try to convert to string if it's not already
                        logger.warning(f"Unexpected response type: {type(content)}. Converting to string.")
                        content_str = str(content)
                        # Cache the result before returning
                        self._guidelines_cache[category_key] = content_str
                        return content_str
                else:
                    logger.warning("No content in Anthropic response")
                    return "No guidelines available"
            
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error generating category guidelines: {e}")
            # Provide a simple fallback
            fallback = f"""
            ### {category} Trivia Question Guidelines

            **Cover diverse topics within {category}**
            Include questions from various sub-domains and time periods within {category}.

            **Include a mix of easy and challenging questions**
            Balance between common knowledge and more specialized information.

            **Focus on factual accuracy**
            Ensure all questions are based on verified information.
            """
            # Don't cache error responses
            return fallback