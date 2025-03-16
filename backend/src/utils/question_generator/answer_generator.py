import json
from config.llm_config import LLMConfigFactory
from models.answer import Answer

class AnswerGenerator:
    """
    Generates answers for trivia questions
    """
    def __init__(self, llm_config=None):
        """
        Initialize the answer generator
        
        Args:
            llm_config (LLMConfig, optional): Specific LLM configuration to use
        """
        # Use provided config or create default
        self.llm_config = llm_config or LLMConfigFactory.create_default()
        self.client = self.llm_config.get_client()
        self.model = self.llm_config.get_model()
        self.provider = self.llm_config.get_provider()
    
    def generate_answers(self, questions, category, batch_size=50):
        """
        Generate answers for a list of questions
        
        Args:
            questions (list[Question]): Question objects
            category (str): Category for context
            batch_size (int): Batch size for processing
            
        Returns:
            list[Answer]: Generated Answer objects
        """
        # Extract question content and metadata
        question_texts = [q.content for q in questions]
        question_ids = [q.id for q in questions]
        
        # Process in batches
        batches = [question_texts[i:i + batch_size] for i in range(0, len(question_texts), batch_size)]
        id_batches = [question_ids[i:i + batch_size] for i in range(0, len(question_ids), batch_size)]
        
        all_answers = []
        
        for batch, id_batch in zip(batches, id_batches):
            # Get raw answer data
            answer_json = self._call_llm_for_answers(batch, category)
            
            try:
                answers_data = json.loads(answer_json)
                
                # Create Answer objects
                for answer_data, question_id in zip(answers_data, id_batch):
                    answer = Answer(
                        question_id=question_id,
                        correct_answer=answer_data["Correct Answer"],
                        incorrect_answers=answer_data["Incorrect Answer Array"],
                    )
                    all_answers.append(answer)
                    
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Error processing answer data: {e}")
        
        return all_answers
    
    def _call_llm_for_answers(self, question_batch, category):
        """
        Call LLM to generate answers for a batch of questions
        
        Args:
            question_batch (list): Batch of question texts
            category (str): Category for context
            
        Returns:
            str: JSON string with answer data
        """
        prompt = f"""
        You are a trivia expert tasked with enriching a set of trivia questions in the {category} category.

        For each question provided, create a complete JSON object containing:
        - The original question text (exactly as provided)
        - The correct answer (verified for accuracy)
        - Three plausible but incorrect answers that follow these guidelines:
        - All incorrect answers must belong to the same category/type as the correct answer
        - If the question has specific constraints (e.g., "Cities starting with B"), all incorrect answers must meet those same constraints
        - Incorrect answers should vary in difficulty to avoid making the correct answer obvious
        - Incorrect answers should be factually incorrect but believable to someone with moderate knowledge of the topic

        FORMAT REQUIREMENTS:
        1. Return ONLY a JSON array of objects with no additional text
        2. Include ALL {len(question_batch)} questions in your response
        3. Follow this exact structure:

        [
            {{
                "Question": "What is the capital of France?",
                "Correct Answer": "Paris",
                "Incorrect Answer Array": ["London", "Rome", "Berlin"],
            }},
            {{
                "Question": "Which planet is known as the Red Planet?",
                "Correct Answer": "Mars",
                "Incorrect Answer Array": ["Venus", "Jupiter", "Saturn"],
            }}
        ]

        DO NOT include explanations, markdown formatting, or any text outside the JSON structure.

        Here is the list of questions:
        """ + "\n".join([f'- \"{q}\"' for q in question_batch])

        try: 
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                if response.choices:
                    content = response.choices[0].message.content
                    return content
                return json.dumps([])  # Return empty JSON array if no response

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from the TextBlock object
                if isinstance(response.content, list) and len(response.content) > 0:
                    text_content = response.content[0].text  # Extract text from the first TextBlock
                    return text_content
                return json.dumps([])  # Return empty JSON array if no response

        except Exception as e:
            raise ValueError(f"Error processing batch: {e}")