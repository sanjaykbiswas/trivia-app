# backend/src/utils/question_generator/category_helper.py
import logging
from config.llm_config import LLMConfigFactory
from repositories.category_repository import CategoryRepository

# Configure logger
logger = logging.getLogger(__name__)

class CategoryHelper:
    """
    Generates category-specific guidelines for question generation
    """
    def __init__(self, llm_config=None, category_repository=None):
        """
        Initialize the category helper
        
        Args:
            llm_config (LLMConfig, optional): Specific LLM configuration to use
            category_repository (CategoryRepository, optional): Repository for category operations
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        
        # Store category repository for lookups
        self.category_repository = category_repository
        
        # Add a cache for guidelines
        self._guidelines_cache = {}
        # Add a cache for category ID to name mapping
        self._category_id_name_cache = {}
    
    async def get_category_repository(self):
        """
        Lazy initialization of category repository if not provided
        
        Returns:
            CategoryRepository: Repository for category operations
        """
        if not self.category_repository:
            from repositories.category_repository import CategoryRepository
            from config.supabase_client import get_supabase_client
            supabase_client = get_supabase_client()
            self.category_repository = CategoryRepository(supabase_client)
        return self.category_repository
    
    async def resolve_category_name(self, category_id: str) -> str:
        """
        Resolve a category name from ID
        
        Args:
            category_id (str): Category ID to look up
            
        Returns:
            str: Category name or the ID if not found
        """
        # Check if it looks like a UUID
        if not category_id or not isinstance(category_id, str) or '-' not in category_id:
            return category_id  # Not an ID, return as is
            
        # Check cache first
        if category_id in self._category_id_name_cache:
            return self._category_id_name_cache[category_id]
            
        try:
            # Look up in database
            repo = await self.get_category_repository()
            category = await repo.get_by_id(category_id)
            
            if category:
                # Store in cache
                self._category_id_name_cache[category_id] = category.name
                return category.name
                
            return category_id  # Not found, return ID as fallback
        except Exception as e:
            logger.error(f"Error resolving category name for ID {category_id}: {e}")
            return category_id  # Return ID on error
    
    async def get_or_create_category_id(self, category_name: str) -> str:
        """
        Get a category ID from name or create if not found
        
        Args:
            category_name (str): Category name to look up or create
            
        Returns:
            str: Category ID
        """
        if not category_name:
            return None
            
        try:
            # Look up in database
            repo = await self.get_category_repository()
            category = await repo.get_or_create_by_name(category_name)
            
            if category:
                # Store in cache
                self._category_id_name_cache[category.id] = category.name
                return category.id
                
            return None  # Should not happen if get_or_create works
        except Exception as e:
            logger.error(f"Error getting/creating category ID for name {category_name}: {e}")
            return None
    
    async def generate_category_guidelines_async(self, category_id_or_name: str) -> str:
        """
        Generate guidelines for creating questions in a specific category (async version)
        
        Args:
            category_id_or_name (str): The category ID or name to generate guidelines for
            
        Returns:
            str: Guidelines text
        """
        # Resolve category name if ID was provided
        category_name = await self.resolve_category_name(category_id_or_name)
            
        # Check cache using resolved name
        category_key = category_name.lower().strip()
        if category_key in self._guidelines_cache:
            logger.info(f"Using cached category guidelines for '{category_name}'")
            return self._guidelines_cache[category_key]
            
        # Generate guidelines using name
        guidelines = self.generate_category_guidelines(category_name)
        
        # Cache using both ID and name if we have both
        self._guidelines_cache[category_key] = guidelines
        
        return guidelines
    
    def generate_category_guidelines(self, category: str):
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