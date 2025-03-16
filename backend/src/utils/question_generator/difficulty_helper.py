from config.llm_config import LLMConfigFactory

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
        # For DifficultyHelper, we might want to use a less expensive model
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
    
    def generate_difficulty_guidelines(self, category):
        """
        Generate guidelines for defining the difficulty of questions in a specific category
        
        Args:
            category (str): The category to generate difficulty guidelines for
            
        Returns:
            str: Guidelines text
        """
        prompt = f"""
        Create 5 distinct difficulty tiers for the category: '{category}'.

        Analyze the unique aspects of '{category}' and develop a progression of difficulty that spans from beginner-friendly to expert-level knowledge. Consider the following:
        - Knowledge progression (casual → specialized → expert)
        - Skill levels required (basic recall → complex analysis)
        - Audience familiarity (general public → dedicated enthusiasts → professionals)
        - Depth of subject matter (common facts → obscure details)
        - Breadth across subcategories within '{category}'

        Format your response exactly as follows:

        ### {Category} Difficulty Tiers

        **Tier 1: [Brief Title]**
        [2-3 sentence description of knowledge level, question types, and target audience]

        **Tier 2: [Brief Title]**
        [2-3 sentence description of knowledge level, question types, and target audience]

        **Tier 3: [Brief Title]**
        [2-3 sentence description of knowledge level, question types, and target audience]

        **Tier 4: [Brief Title]**
        [2-3 sentence description of knowledge level, question types, and target audience]

        **Tier 5: [Brief Title]**
        [2-3 sentence description of knowledge level, question types, and target audience]

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