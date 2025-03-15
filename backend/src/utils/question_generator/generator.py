import json
from config.llm_config import LLMConfig
from utils.question_generator.category_helper import CategoryHelper
from models.question import Question

class QuestionGenerator:
    """
    Generates trivia questions for given categories
    Refactored from create_questions.py
    """
    def __init__(self):
        self.llm_config = LLMConfig()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
        self.category_helper = CategoryHelper()
    
    def generate_questions(self, category, count=10):
        """
        Generate trivia questions for a specific category
        
        Args:
            category (str): The category to generate questions for
            count (int): Number of questions to generate
            
        Returns:
            list[Question]: Generated Question objects
        """
        # Get category-specific guidelines
        category_guidelines = self.category_helper.generate_category_guidelines(category)
        
        # Generate raw questions
        raw_questions = self._call_llm_for_questions(category, count, category_guidelines)
        
        # Parse questions and convert to Question objects
        if isinstance(raw_questions, str):
            try:
                question_list = json.loads(raw_questions)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON response from LLM")
        else:
            question_list = raw_questions
            
        # Create Question objects
        return [Question(content=q, category=category) for q in question_list]
    
    def _call_llm_for_questions(self, category, count, category_guidelines):
        """
        Call the LLM to generate questions
        
        Args:
            category (str): Category
            count (int): Number of questions
            category_guidelines (str): Category-specific guidelines
            
        Returns:
            str or list: Raw question data from LLM
        """
        prompt = f"""
        Generate {count} trivia questions for the category '{category}'.  Ensure each question is unique.
        
        Follow these primary guidelines when creating a response:

        **Output format**
        -- Output the answers in valid JSON format.
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

        **Difficulty**
        -- Provide questions with a range of difficulties, but overall lean towards more challenging.

        Additionally, ensure you follow the following more specific guidelines for the category '{category}':

        {category_guidelines}

        Your overall goal is to create trivia questions that are not only educational and engaging but also diverse in style and difficulty. Make sure each question is unique, fun, thought-provoking, and follows the above guidelines.
        """
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")