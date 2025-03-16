from config.llm_config import LLMConfigFactory

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
        # For CategoryHelper, we might want to use a less expensive model
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
    
    def generate_category_guidelines(self, category):
        """
        Generate guidelines for creating questions in a specific category
        
        Args:
            category (str): The category to generate guidelines for
            
        Returns:
            str: Guidelines text
        """
        prompt = f"""
        Create a comprehensive guide for generating exceptional trivia questions in the category: '{category}'.

        Analyze the distinctive elements of '{category}' and develop specific guidelines that will help create engaging, accurate, and diverse trivia questions. Focus on:

        - Key knowledge domains within this category
        - Different question formats that work well
        - Types of facts that make for interesting questions
        - Ways to ensure questions are factually accurate

        Format your response using the exact structure below:

        ### {category} Trivia Question Guidelines

        **[Descriptive Guideline Title 1]**
        Clear explanation of the guideline.

        **[Descriptive Guideline Title 2]**
        Clear explanation of the guideline.

        [Continue with additional guidelines, maximum of 10 total]

        Important: Do not include guidelines about visual questions or difficulty balancing. Focus exclusively on content, format, and quality considerations for text-based trivia questions.
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
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")