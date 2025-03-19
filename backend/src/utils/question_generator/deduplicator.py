import numpy as np
import logging
from openai import OpenAI
from config.environment import Environment
from models.question import Question

# Configure logger
logger = logging.getLogger(__name__)

class Deduplicator:
    """
    Removes duplicate questions using embeddings
    Refactored from remove_duplicates.py
    """
    def __init__(self):
        env = Environment()
        self.openai_client = OpenAI(api_key=env.get("openai_api_key"))
        self.embedding_model = "text-embedding-3-small"
    
    def remove_duplicates(self, questions, threshold=0.90):
        """
        Remove duplicate questions based on semantic similarity
        
        Args:
            questions (list[Question]): List of Question objects
            threshold (float): Similarity threshold for duplicates
            
        Returns:
            list[Question]: Deduplicated questions
        """
        # Check if we have questions to process
        if not questions or len(questions) <= 1:
            return questions
            
        # Extract question content
        question_texts = [q.content for q in questions]
        
        try:
            # Get embeddings
            embeddings = self._get_embeddings(question_texts)
            
            # Find duplicates
            duplicate_indices = set()
            num_questions = len(embeddings)

            for i in range(num_questions):
                if i in duplicate_indices:
                    continue
                for j in range(i + 1, num_questions):
                    if j in duplicate_indices:
                        continue
                    if self._cosine_similarity(embeddings[i], embeddings[j]) > threshold:
                        duplicate_indices.add(j)
            
            # Return non-duplicate questions
            return [q for idx, q in enumerate(questions) if idx not in duplicate_indices]
            
        except Exception as e:
            logger.error(f"Error in deduplication process: {e}")
            # If embedding fails, just return the original questions
            logger.warning("Returning original questions without deduplication due to error")
            return questions
    
    def _get_embeddings(self, texts):
        """
        Get embeddings for a list of texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            list: List of embedding vectors
        """
        if not texts:
            return []
            
        # Ensure all items are strings
        processed_texts = []
        for text in texts:
            if not isinstance(text, str):
                logger.warning(f"Converting non-string item to string: {type(text)}")
                processed_texts.append(str(text))
            else:
                processed_texts.append(text)
        
        try:
            logger.info(f"Getting embeddings for {len(processed_texts)} texts")
            
            # Process texts in batches to avoid API limitations
            batch_size = 100  # OpenAI recommends batches of 100 or fewer
            all_embeddings = []
            
            for i in range(0, len(processed_texts), batch_size):
                batch = processed_texts[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} of {(len(processed_texts)-1)//batch_size + 1}")
                
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            # Raise the exception to be handled by the caller
            raise
    
    def _cosine_similarity(self, vec1, vec2):
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1 (list): First vector
            vec2 (list): Second vector
            
        Returns:
            float: Similarity score
        """
        vec1, vec2 = np.array(vec1), np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))