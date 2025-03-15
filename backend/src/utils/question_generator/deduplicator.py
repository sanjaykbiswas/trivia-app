import numpy as np
from openai import OpenAI
from config.environment import Environment
from models.question import Question

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
        # Extract question content
        question_texts = [q.content for q in questions]
        
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
    
    def _get_embeddings(self, texts):
        """
        Get embeddings for a list of texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            list: List of embedding vectors
        """
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
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