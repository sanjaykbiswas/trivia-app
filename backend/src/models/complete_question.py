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
    def category(self):
        return self.question.category
    
    def to_dict(self):
        """Convert to a single dictionary"""
        return {
            "id": self.question.id,
            "content": self.question.content,
            "category": self.question.category,
            "correct_answer": self.answer.correct_answer,
            "incorrect_answers": self.answer.incorrect_answers,
            "difficulty": self.question.difficulty,
            "created_at": self.question.created_at.isoformat()
        }