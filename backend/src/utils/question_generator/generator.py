import json
import logging
from config.llm_config import LLMConfigFactory
from utils.question_generator.category_helper import CategoryHelper
from utils.question_generator.difficulty_helper import DifficultyHelper
from models.question import Question
from utils.json_parsing import JSONParsingUtils  # Import the new utility

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
        
        # CategoryHelper can use its own LLM configuration if needed
        self.category_helper = CategoryHelper()
        self.difficulty_helper = DifficultyHelper()
        
        # Standard difficulty levels (5 tiers)
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    def generate_questions(self, category, count=10, difficulty=None):
        """
        Generate trivia questions for a specific category
        
        Args:
            category (str): The category to generate questions for
            count (int): Number of questions to generate
            difficulty (str or int, optional): Specific difficulty level to target
                                              (Easy, Medium, Hard, Expert, Master) or tier number (1-5)
            
        Returns:
            list[Question]: Generated Question objects
        """
        # Get category-specific guidelines
        category_guidelines = self.category_helper.generate_category_guidelines(category)
        
        # Standardize difficulty if provided
        standard_difficulty = None
        difficulty_context = ""
        
        if difficulty:
            # Convert to standard difficulty format
            if isinstance(difficulty, int) and 1 <= difficulty <= 5:
                standard_difficulty = self.difficulty_levels[difficulty-1]
            elif isinstance(difficulty, str) and difficulty in self.difficulty_levels:
                standard_difficulty = difficulty
            elif isinstance(difficulty, str):
                # Try to match difficulty string to standard level
                for level in self.difficulty_levels:
                    if level.lower() in difficulty.lower():
                        standard_difficulty = level
                        break
                
            # If still not matched, default to Medium
            if not standard_difficulty:
                standard_difficulty = "Medium"
                
            # Generate all difficulty tiers
            difficulty_tiers = self.difficulty_helper.generate_difficulty_guidelines(category)
            
            # Get the specific tier description requested
            if difficulty_tiers:
                difficulty_context = self.difficulty_helper.get_difficulty_by_tier(difficulty_tiers, standard_difficulty)
                if difficulty_context:
                    difficulty_context = f"\nDifficulty Level:\n{difficulty_context}"
        
        # Generate raw questions
        raw_response = self._call_llm_for_questions(category, count, category_guidelines, difficulty_context)
        
        # Use the new robust JSON parsing utility
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