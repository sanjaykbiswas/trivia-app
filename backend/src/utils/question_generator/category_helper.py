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
        Generate a prompt that will help a **Trivia Question Generator** LLM come up with interesting trivia questions for the category '{category}'.

        The prompt should consider the nuances of '{category}', and frame these nuances in a way that will help the **Trivia Question Generator** create high-quality questions.

        Return clear, labeled guidelines in the following format, and limit the number of guidelines you create to 10. Don't output anything but the format described below.

        Category Guidelines

        **Guideline 1** Description of guideline 1 (Replace **Guideline 1** with a label for the guideline)

        **Guideline 2** Description of guideline 2 (Replace **Guideline 2** with a label for the guideline)

        **Guideline N** Description of guideline N (Replace **Guideline N** with a label for the guideline)

        --
        None of the guidelines should involve visual question generation or difficulty balancing.
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