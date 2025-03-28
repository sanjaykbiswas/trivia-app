from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from models.question import Question
from models.answer import Answer

@dataclass
class CompleteQuestion:
    """
    Combined model with question and answer data
    """
    question: Question
    answer: Answer
    
    @property
    def content(self):
        return self.question.content
    
    @property
    def correct_answer(self):
        return self.answer.correct_answer
    
    @property
    def incorrect_answers(self):
        return self.answer.incorrect_answers
    
    @property
    def difficulty(self):
        return self.question.difficulty
    
    @property
    def modified_difficulty(self):
        return self.question.modified_difficulty
    
    @property
    def category_id(self):
        return self.question.category_id
    
    @property
    def category_name(self):
        return self.question.category_name
    
    def to_dict(self):
        """Convert to a single dictionary"""
        return {
            "id": self.question.id,
            "content": self.question.content,
            "category_id": self.question.category_id,
            "category_name": self.question.category_name,
            "correct_answer": self.answer.correct_answer,
            "incorrect_answers": self.answer.incorrect_answers,
            "difficulty": self.question.difficulty,
            "modified_difficulty": self.question.modified_difficulty,
            "created_at": self.question.created_at.isoformat()
        }