from config.llm_config import LLMConfigFactory
import json
import re

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
        
        # Five standard difficulty levels
        self.difficulty_levels = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    def generate_difficulty_guidelines(self, category):
        """
        Generate guidelines for defining the difficulty of questions in a specific category
        
        Args:
            category (str): The category to generate difficulty guidelines for
            
        Returns:
            dict: Structured difficulty guidelines with keys for each tier
        """
        prompt = f"""
        Create 5 distinct difficulty tiers for the category: '{category}'.

        Analyze the unique aspects of '{category}' and develop a progression of difficulty that spans from beginner-friendly to expert-level knowledge. Consider the following:
        - Knowledge progression (casual → specialized → expert)
        - Skill levels required (basic recall → complex analysis)
        - Audience familiarity (general public → dedicated enthusiasts → professionals)
        - Depth of subject matter (common facts → obscure details)
        - Breadth across subcategories within '{category}'

        Format your response in a way that can be automatically parsed as JSON, following this exact structure:

        {{
            "Easy": "2-3 sentence description of knowledge level, question types, and target audience",
            "Medium": "2-3 sentence description of knowledge level, question types, and target audience",
            "Hard": "2-3 sentence description of knowledge level, question types, and target audience",
            "Expert": "2-3 sentence description of knowledge level, question types, and target audience",
            "Master": "2-3 sentence description of knowledge level, question types, and target audience"
        }}

        Ensure you include all 5 tiers exactly as named above and provide detailed, unique descriptions for each level.
        """
        
        raw_response = ""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_response = response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_response = response.content[0].text
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        # Parse the response into a structured format
        return self._parse_difficulty_response(raw_response)
    
    def _parse_difficulty_response(self, raw_response):
        """
        Parse the LLM response into a structured format
        
        Args:
            raw_response (str): Raw text response from the LLM
            
        Returns:
            dict: Structured difficulty guidelines
        """
        # Try to parse as JSON first
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass
        
        # Fall back to regex parsing if JSON parsing fails
        structured_difficulties = {}
        
        # Clean up the response - find content between triple backticks if present
        json_content = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_response, re.DOTALL)
        if json_content:
            try:
                return json.loads(json_content.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract using regex as a last resort
        for level in self.difficulty_levels:
            pattern = rf'"{level}":\s*"(.*?)"(?=,|\s*}})'
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                description = match.group(1).strip()
                structured_difficulties[level] = description
        
        # If we couldn't parse the structure properly, create a default structure
        if not structured_difficulties:
            for level in self.difficulty_levels:
                structured_difficulties[level] = f"Default {level.lower()} difficulty for {level.lower()} questions."
        
        return structured_difficulties
    
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