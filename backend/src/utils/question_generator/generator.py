import json
import logging
import asyncio
from config.llm_config import LLMConfigFactory
from utils.question_generator.category_helper import CategoryHelper
from utils.question_generator.difficulty_helper import DifficultyHelper
from models.question import Question
from utils.json_parsing import JSONParsingUtils

# Configure logger
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Generates trivia questions for given categories
    """
    def __init__(self, llm_config=None):
        """
        Initialize the question generator
        
        Args:
            llm_config (LLMConfig, optional): Specific LLM configuration to use
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        
        # CategoryHelper and DifficultyHelper can use their own LLM configuration
        self.category_helper = CategoryHelper(self.llm_config)
        self.difficulty_helper = DifficultyHelper(self.llm_config)
        
        # Standard difficulty levels (5 tiers)
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    async def _fetch_guidelines_concurrently(self, category, difficulty=None):
        """
        Fetch category guidelines and difficulty tiers concurrently
        
        Args:
            category (str): The category to generate guidelines for
            difficulty (str, optional): Specific difficulty level
            
        Returns:
            tuple: (category_guidelines, difficulty_context)
        """
        # Create tasks for concurrent execution
        category_task = asyncio.create_task(
            self._get_category_guidelines(category)
        )
        
        difficulty_task = None
        if difficulty:
            difficulty_task = asyncio.create_task(
                self._get_difficulty_context(category, difficulty)
            )
        
        # Wait for category guidelines
        category_guidelines = await category_task
        
        # Wait for difficulty context if needed
        difficulty_context = ""
        if difficulty_task:
            difficulty_context = await difficulty_task
        
        return category_guidelines, difficulty_context
    
    async def _get_category_guidelines(self, category):
        """
        Get category-specific guidelines asynchronously
        
        Args:
            category (str): The category to generate guidelines for
            
        Returns:
            str: Guidelines text
        """
        # Wrap the synchronous method in an executor to make it async
        return await asyncio.to_thread(
            self.category_helper.generate_category_guidelines,
            category
        )
    
    async def _get_difficulty_context(self, category, difficulty):
        """
        Get difficulty-specific context asynchronously
        
        Args:
            category (str): The category
            difficulty (str): The difficulty level
            
        Returns:
            str: Difficulty context
        """
        # Standardize difficulty
        standard_difficulty = self._standardize_difficulty(difficulty)
        
        # Generate all difficulty tiers
        difficulty_tiers = await asyncio.to_thread(
            self.difficulty_helper.generate_difficulty_guidelines,
            category
        )
        
        # Get the specific tier description
        if difficulty_tiers:
            difficulty_context = self.difficulty_helper.get_difficulty_by_tier(
                difficulty_tiers, 
                standard_difficulty
            )
            if difficulty_context:
                return f"\nDifficulty Level:\n{difficulty_context}"
        
        return ""
    
    def _standardize_difficulty(self, difficulty):
        """
        Convert difficulty input to standard format
        
        Args:
            difficulty: Input difficulty (str or int)
            
        Returns:
            str: Standardized difficulty level
        """
        # Convert to standard difficulty format
        if isinstance(difficulty, int) and 1 <= difficulty <= 5:
            return self.difficulty_levels[difficulty-1]
        elif isinstance(difficulty, str) and difficulty in self.difficulty_levels:
            return difficulty
        elif isinstance(difficulty, str):
            # Try to match difficulty string to standard level
            for level in self.difficulty_levels:
                if level.lower() in difficulty.lower():
                    return level
            
        # Default to Medium if not matched
        return "Medium"
    
    async def generate_questions_async(self, category, count=10, difficulty=None):
        """
        Generate trivia questions for a specific category (async version)
        
        Args:
            category (str): The category to generate questions for
            count (int): Number of questions to generate
            difficulty (str or int, optional): Specific difficulty level
            
        Returns:
            list[Question]: Generated Question objects
        """
        # Get guidelines concurrently
        category_guidelines, difficulty_context = await self._fetch_guidelines_concurrently(
            category, 
            difficulty
        )
        
        # Standardize difficulty if provided
        standard_difficulty = None
        if difficulty:
            standard_difficulty = self._standardize_difficulty(difficulty)
        
        # Generate raw questions
        raw_response = await asyncio.to_thread(
            self._call_llm_for_questions,
            category, 
            count, 
            category_guidelines, 
            difficulty_context
        )
        
        # Parse and process questions
        return self._process_raw_questions(raw_response, category, count, standard_difficulty)
    
    def generate_questions(self, category, count=10, difficulty=None):
        """
        Generate trivia questions for a specific category (sync wrapper)
        
        Args:
            category (str): The category to generate questions for
            count (int): Number of questions to generate
            difficulty (str or int, optional): Specific difficulty level
            
        Returns:
            list[Question]: Generated Question objects
        """
        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async version in the event loop
        return loop.run_until_complete(
            self.generate_questions_async(category, count, difficulty)
        )
    
    def _process_raw_questions(self, raw_response, category, count, standard_difficulty):
        """
        Process raw questions from LLM response
        
        Args:
            raw_response: Raw LLM response
            category (str): Question category
            count (int): Requested count
            standard_difficulty (str): Standardized difficulty level
            
        Returns:
            list[Question]: Question objects
        """
        try:
            # Check if raw_response is already a Python object (list)
            if isinstance(raw_response, list):
                question_list = raw_response
                logger.info("LLM response was already a list, no parsing needed")
            else:
                # Extract and parse the JSON with fallbacks
                parsed_data = JSONParsingUtils.parse_json_with_fallbacks(
                    raw_response, 
                    default_value=[]
                )
                
                # Ensure it's a list structure
                question_list = JSONParsingUtils.ensure_list_structure(parsed_data)
            
            # Validate and clean the question format
            question_list = JSONParsingUtils.validate_question_format(question_list)
            
            # Handle truncation by limiting to the requested count
            if len(question_list) > count:
                question_list = question_list[:count]
                
            # Log the final count
            logger.info(f"Successfully parsed {len(question_list)} questions out of {count} requested")
                
            # Create Question objects with difficulty information
            return [Question(content=q, category=category, difficulty=standard_difficulty) 
                    for q in question_list]
        
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            # Return an empty list if parsing completely fails
            return []
    
    def _call_llm_for_questions(self, category, count, category_guidelines, difficulty_context=""):
        """
        Call the LLM to generate questions
        
        Args:
            category (str): Category
            count (int): Number of questions
            category_guidelines (str): Category-specific guidelines
            difficulty_context (str): Difficulty-specific context
            
        Returns:
            str or list: Raw question data from LLM
        """
        prompt = f"""
        Generate {count} trivia questions for the category '{category}'.  Ensure each question is unique.
        
        Follow these primary guidelines when creating a response:

        **Output format**
        -- Output the questions in valid JSON format.
        -- One-dimensional JSON array of strings.  Do not nest the questions under a key.
        -- No markdown, fluff, introductions, or finishes.
        -- Output the questions only, no answers.
        -- Do not number the questions.
        -- Example format below:

        [
          "Question?",
          "Question?",
          "Question?"
        ]

        **Question Style**
        -- Trivia style, but keep the question style somewhat diverse so it is not monotonous.
        -- Ensure questions are suitable for multiple-choice trivia answers (e.g., the correct answer should not be a paragraph long)
        -- Do not do riddles.
        -- Avoid ambiguity in questions.
        -- Ensure questions are well-phrased, avoiding jargon or overly complex language that might confuse participants. 
        --Aim for succinct questions that clearly define what is being asked, reducing the chance of multiple interpretations and leading to a more straightforward answering process.
        
        **Difficulty**
        -- Questions should match the difficulty context, if provided: {difficulty_context}.

        Additionally, ensure you follow the following more specific guidelines for the category '{category}':

        {category_guidelines}

        Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is unique, fun, thought-provoking, and follows the above guidelines.
        
        IMPORTANT: All output MUST be valid JSON. Do not include any text before or after the JSON array.
        """
        
        try:
            logger.info(f"Using model: {self.model} from provider: {self.provider}")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                logger.info(f"Raw LLM Response: {response.choices[0].message.content[:100]}...")
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                logger.info(f"Raw LLM Response: {response.content[0].text[:100]}...")
                return response.content[0].text
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return "[]"  # Return empty JSON array string as fallback