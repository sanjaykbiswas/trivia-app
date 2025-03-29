# backend/src/repositories/upload_repository.py
from typing import List, Dict, Any, Optional, Tuple
import logging
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from repositories.base_repository_impl import BaseRepositoryImpl

# Configure logger
logger = logging.getLogger(__name__)

class UploadRepository:
    """
    Repository for handling uploads of questions and answers to the database
    
    Note: This doesn't extend BaseRepositoryImpl as it doesn't map to a single table,
    but rather orchestrates operations across multiple tables.
    """
    def __init__(self, supabase_client):
        """
        Initialize with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.client = supabase_client
        self.questions_table = "questions"
        self.answers_table = "answers"
        
        # Create internal repositories for each table
        self._question_repo = BaseRepositoryImpl(
            supabase_client, 
            self.questions_table, 
            Question
        )
        
        self._answer_repo = BaseRepositoryImpl(
            supabase_client, 
            self.answers_table, 
            Answer
        )
    
    async def save_question(self, question: Question) -> Question:
        """
        Save a question to the database
        
        Args:
            question (Question): Question object to save
            
        Returns:
            Question: Saved question with ID
        """
        logger.info(f"Saving question: {question.content[:30]}...")
        
        # Use internal repository to save question
        saved_question = await self._question_repo.create(question)
        
        if saved_question and saved_question.id:
            logger.info(f"Question saved with ID: {saved_question.id}")
        else:
            logger.error("Failed to save question")
        
        return saved_question
    
    async def save_answer(self, answer: Answer) -> Answer:
        """
        Save an answer to the database
        
        Args:
            answer (Answer): Answer object to save
            
        Returns:
            Answer: Saved answer with ID
        """
        logger.info(f"Saving answer for question ID: {answer.question_id}")
        
        # Use internal repository to save answer
        saved_answer = await self._answer_repo.create(answer)
        
        if saved_answer and saved_answer.id:
            logger.info(f"Answer saved with ID: {saved_answer.id}")
        else:
            logger.error("Failed to save answer")
        
        return saved_answer
    
    async def save_question_and_answer(self, question: Question, answer: Answer) -> Dict[str, Any]:
        """
        Save both question and answer objects to the database
        
        Args:
            question (Question): Question object to save
            answer (Answer): Answer object to save (without question_id)
            
        Returns:
            Dict[str, Any]: Dictionary with saved question and answer objects
        """
        # Save question first
        saved_question = await self.save_question(question)
        
        # Set question_id on answer
        answer.question_id = saved_question.id
        
        # Save answer
        saved_answer = await self.save_answer(answer)
        
        return {
            "question": saved_question,
            "answer": saved_answer
        }
    
    async def bulk_save_questions_and_answers(
        self, 
        questions: List[Question], 
        answers: List[Answer]
    ) -> List[Dict[str, Any]]:
        """
        Save multiple question and answer pairs to the database
        
        Args:
            questions (List[Question]): List of question objects
            answers (List[Answer]): List of answer objects (without question_ids)
            
        Returns:
            List[Dict[str, Any]]: List of dictionaries with saved question and answer objects
        """
        if len(questions) != len(answers):
            raise ValueError("Number of questions and answers must match")
        
        # Save questions in bulk
        saved_questions = await self._question_repo.bulk_create(questions)
        
        # Update answer question_ids and save in bulk
        for i, answer in enumerate(answers):
            answer.question_id = saved_questions[i].id
        
        saved_answers = await self._answer_repo.bulk_create(answers)
        
        # Combine results
        results = []
        for i in range(len(saved_questions)):
            results.append({
                "question": saved_questions[i],
                "answer": saved_answers[i]
            })
        
        return results
    
    async def save_complete_question(self, complete_question: CompleteQuestion) -> CompleteQuestion:
        """
        Save a complete question (question and answer) to the database
        
        Args:
            complete_question (CompleteQuestion): Complete question to save
            
        Returns:
            CompleteQuestion: Saved complete question with IDs
        """
        # Extract question and answer
        question = complete_question.question
        answer = complete_question.answer
        
        # Save both
        result = await self.save_question_and_answer(question, answer)
        
        # Create new CompleteQuestion with saved objects
        return CompleteQuestion(
            question=result["question"],
            answer=result["answer"]
        )
    
    async def bulk_save_complete_questions(
        self,
        complete_questions: List[CompleteQuestion]
    ) -> List[CompleteQuestion]:
        """
        Save multiple complete questions to the database
        
        Args:
            complete_questions (List[CompleteQuestion]): List of complete questions to save
            
        Returns:
            List[CompleteQuestion]: Saved complete questions with IDs
        """
        # Extract questions and answers
        questions = [cq.question for cq in complete_questions]
        answers = [cq.answer for cq in complete_questions]
        
        # Save in bulk
        results = await self.bulk_save_questions_and_answers(questions, answers)
        
        # Create new CompleteQuestions with saved objects
        saved_complete_questions = []
        for result in results:
            saved_complete_questions.append(
                CompleteQuestion(
                    question=result["question"],
                    answer=result["answer"]
                )
            )
        
        return saved_complete_questions