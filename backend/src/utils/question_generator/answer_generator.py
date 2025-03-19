import json
import logging
from config.llm_config import LLMConfigFactory
from models.answer import Answer
from utils.json_parsing import JSONParsingUtils

# Configure logger
logger = logging.getLogger(__name__)

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
        # Check if we have any questions to process
        if not questions:
            logger.warning("No questions provided for answer generation")
            return []
            
        # Extract question content and metadata
        question_texts = [q.content for q in questions]
        question_ids = [q.id for q in questions]
        
        # Process in batches
        batches = [question_texts[i:i + batch_size] for i in range(0, len(question_texts), batch_size)]
        id_batches = [question_ids[i:i + batch_size] for i in range(0, len(question_ids), batch_size)]
        
        all_answers = []
        
        for batch_idx, (batch, id_batch) in enumerate(zip(batches, id_batches)):
            logger.info(f"Processing answer batch {batch_idx+1}/{len(batches)} ({len(batch)} questions)")
            
            # Get raw answer data
            raw_response = self._call_llm_for_answers(batch, category)
            
            try:
                # Check if raw_response is already a Python object (list or dict)
                if isinstance(raw_response, (list, dict)):
                    parsed_data = raw_response
                    logger.info("LLM response was already a Python object, no parsing needed")
                else:
                    # Use the robust JSON parsing utility
                    parsed_data = JSONParsingUtils.parse_json_with_fallbacks(
                        raw_response, 
                        default_value=[]
                    )
                
                # Ensure it's a list structure
                answers_data = JSONParsingUtils.ensure_list_structure(parsed_data)
                
                # Validate and standardize the answer format
                answers_data = JSONParsingUtils.validate_answer_format(answers_data)
                
                logger.info(f"Successfully parsed {len(answers_data)} answers in batch {batch_idx+1}")
                
                # Create Answer objects
                for answer_idx, (answer_data, question_id) in enumerate(zip(answers_data, id_batch)):
                    if 'correct_answer' in answer_data and 'incorrect_answers' in answer_data:
                        try:
                            # Validate that we have the required data in correct format
                            correct_answer = str(answer_data["correct_answer"])
                            
                            # Ensure incorrect_answers is a list of strings
                            incorrect_answers = []
                            for ans in answer_data["incorrect_answers"]:
                                incorrect_answers.append(str(ans))
                            
                            # Create the Answer object
                            answer = Answer(
                                question_id=question_id,
                                correct_answer=correct_answer,
                                incorrect_answers=incorrect_answers
                            )
                            all_answers.append(answer)
                        except Exception as e:
                            logger.error(f"Error creating answer for question {answer_idx}: {e}")
                    else:
                        logger.warning(f"Missing required fields in answer data for question {answer_idx}")
                    
            except Exception as e:
                logger.error(f"Error processing answer batch {batch_idx+1}: {e}")
                # Continue with the next batch rather than failing entirely
        
        logger.info(f"Generated {len(all_answers)} answers for {len(questions)} questions")
        return all_answers
    
    def _call_llm_for_answers(self, question_batch, category):
        """
        Call LLM to generate answers for a batch of questions
        
        Args:
            question_batch (list): Batch of question texts
            category (str): Category for context
            
        Returns:
            str or dict/list: Raw answer data from LLM
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
        IMPORTANT: All output MUST be valid JSON. Do not include any text before or after the JSON array.

        Here is the list of questions:
        """ + "\n".join([f'- \"{q}\"' for q in question_batch])

        try: 
            logger.info(f"Calling {self.provider} model {self.model} for answer generation")
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                if response.choices:
                    logger.info(f"Received response from {self.provider}")
                    return response.choices[0].message.content
                return "[]"  # Return empty JSON array if no response

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from the TextBlock object
                if isinstance(response.content, list) and len(response.content) > 0:
                    logger.info(f"Received response from {self.provider}")
                    return response.content[0].text
                return "[]"  # Return empty JSON array if no response

        except Exception as e:
            logger.error(f"Error calling LLM for answer generation: {e}")
            return "[]"  # Return empty JSON array on error