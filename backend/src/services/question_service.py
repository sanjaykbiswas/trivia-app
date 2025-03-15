from typing import List, Dict, Any, Optional
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.question_repository import QuestionRepository
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator

class QuestionService:
    """
    Service for managing trivia questions
    
    This orchestrates all operations related to questions, including:
    - Generation
    - Storage
    - Retrieval
    - Game mechanics
    """
    def __init__(
        self, 
        question_repository: QuestionRepository,
        question_generator: QuestionGenerator,
        answer_generator: AnswerGenerator,
        deduplicator: Deduplicator
    ):
        self.repository = question_repository
        self.generator = question_generator
        self.answer_generator = answer_generator
        self.deduplicator = deduplicator
    
    def generate_and_save_questions(
        self, 
        category: str, 
        count: int = 10,
        deduplicate: bool = True
    ) -> List[Question]:
        """
        Generate questions for a category and save them
        
        Args:
            category (str): Question category
            count (int): Number of questions to generate
            deduplicate (bool): Whether to deduplicate questions
            
        Returns:
            List[Question]: Generated and saved questions
        """
        # Generate questions
        questions = self.generator.generate_questions(category, count)
        
        # Deduplicate if requested
        if deduplicate:
            questions = self.deduplicator.remove_duplicates(questions)
        
        # Save to database
        saved_questions = self.repository.bulk_create(questions)
        
        return saved_questions
    
    def generate_answers_for_questions(
        self,
        questions: List[Question],
        category: str,
        batch_size: int = 50
    ) -> List[Answer]:
        """
        Generate and save answers for questions
        
        Args:
            questions (List[Question]): Questions to generate answers for
            category (str): Category for context
            batch_size (int): Processing batch size
            
        Returns:
            List[Answer]: Generated answers
        """
        # Generate answers
        answers = self.answer_generator.generate_answers(
            questions=questions,
            category=category,
            batch_size=batch_size
        )
        
        # Save answers
        saved_answers = self.repository.bulk_save_answers(answers)
        
        return saved_answers
    
    def create_complete_question_set(
        self,
        category: str,
        count: int = 10,
        deduplicate: bool = True,
        batch_size: int = 50
    ) -> List[CompleteQuestion]:
        """
        Complete end-to-end pipeline: generate questions and answers
        
        Args:
            category (str): Question category
            count (int): Number of questions
            deduplicate (bool): Whether to deduplicate
            batch_size (int): Processing batch size
            
        Returns:
            List[CompleteQuestion]: Complete questions with answers
        """
        # Generate and save questions
        questions = self.generate_and_save_questions(
            category=category,
            count=count,
            deduplicate=deduplicate
        )
        
        # Generate and save answers
        answers = self.generate_answers_for_questions(
            questions=questions,
            category=category,
            batch_size=batch_size
        )
        
        # Create complete questions from questions and answers
        complete_questions = []
        answer_map = {a.question_id: a for a in answers}
        
        for question in questions:
            if question.id in answer_map:
                complete_question = CompleteQuestion(
                    question=question,
                    answer=answer_map[question.id]
                )
                complete_questions.append(complete_question)
        
        return complete_questions
    
    def get_questions_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Question]:
        """
        Retrieve questions by category
        
        Args:
            category (str): Category to filter by
            limit (int): Maximum results
            
        Returns:
            List[Question]: Matching questions
        """
        return self.repository.find_by_category(category, limit)
    
    def get_random_game_questions(
        self,
        categories=None,
        count: int = 10
    ) -> List[CompleteQuestion]:
        """
        Get random questions for a game
        
        Args:
            categories (List[str], optional): Categories to include
            count (int): Number of questions
            
        Returns:
            List[CompleteQuestion]: Random questions with answers
        """
        return self.repository.get_random_game_questions(categories, count)
    
    def get_complete_question(
        self,
        question_id: str
    ) -> Optional[CompleteQuestion]:
        """
        Get a complete question with its answer
        
        Args:
            question_id (str): Question ID
            
        Returns:
            Optional[CompleteQuestion]: Complete question if found
        """
        return self.repository.get_complete_question(question_id)