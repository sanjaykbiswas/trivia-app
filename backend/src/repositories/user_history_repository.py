from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models.user_question_history import UserQuestionHistory
from models.user_category_history import UserCategoryHistory
from repositories.base_repository import BaseRepository

class UserHistoryRepository:
    """
    Repository for managing user history in the database
    """
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.question_history_table = "user_question_history"
        self.category_history_table = "user_category_history"
    
    # Question History Methods
    
    async def add_question_history(self, history: UserQuestionHistory) -> UserQuestionHistory:
        """Add a question view to user history"""
        response = (
            self.client
            .table(self.question_history_table)
            .insert(history.to_dict())
            .execute()
        )
        
        if response.data:
            history.id = response.data[0]["id"]
        
        return history
    
    async def get_user_question_history(self, user_id: str, limit: int = 100) -> List[UserQuestionHistory]:
        """Get question history for a user"""
        response = (
            self.client
            .table(self.question_history_table)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [UserQuestionHistory.from_dict(data) for data in response.data]
    
    async def has_user_seen_question(self, user_id: str, question_id: str) -> bool:
        """Check if a user has seen a specific question"""
        response = (
            self.client
            .table(self.question_history_table)
            .select("id")
            .eq("user_id", user_id)
            .eq("question_id", question_id)
            .execute()
        )
        
        return len(response.data) > 0
    
    async def get_user_correct_answers(self, user_id: str) -> int:
        """Get count of correct answers for a user"""
        response = (
            self.client
            .table(self.question_history_table)
            .select("id")
            .eq("user_id", user_id)
            .eq("correct", True)
            .execute()
        )
        
        return len(response.data)
    
    async def get_questions_seen_by_user(self, user_id: str) -> List[str]:
        """Get IDs of all questions seen by a user"""
        response = (
            self.client
            .table(self.question_history_table)
            .select("question_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        return [record["question_id"] for record in response.data]
    
    # Category History Methods
    
    async def add_category_play(self, user_id: str, category: str) -> UserCategoryHistory:
        """Add or update category play history"""
        # Check if history already exists
        response = (
            self.client
            .table(self.category_history_table)
            .select("*")
            .eq("user_id", user_id)
            .eq("category", category)
            .execute()
        )
        
        if response.data:
            # Update existing record
            existing = UserCategoryHistory.from_dict(response.data[0])
            existing.play_count += 1
            existing.last_played_at = datetime.now()
            
            update_response = (
                self.client
                .table(self.category_history_table)
                .update({
                    "play_count": existing.play_count,
                    "last_played_at": existing.last_played_at.isoformat()
                })
                .eq("id", existing.id)
                .execute()
            )
            
            if update_response.data:
                return UserCategoryHistory.from_dict(update_response.data[0])
            return existing
        else:
            # Create new record
            new_history = UserCategoryHistory(
                user_id=user_id,
                category=category,
                play_count=1
            )
            
            create_response = (
                self.client
                .table(self.category_history_table)
                .insert(new_history.to_dict())
                .execute()
            )
            
            if create_response.data:
                new_history.id = create_response.data[0]["id"]
            
            return new_history
    
    async def get_user_category_history(self, user_id: str, limit: int = 20) -> List[UserCategoryHistory]:
        """Get category history for a user"""
        response = (
            self.client
            .table(self.category_history_table)
            .select("*")
            .eq("user_id", user_id)
            .order("last_played_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [UserCategoryHistory.from_dict(data) for data in response.data]
    
    async def get_user_favorite_categories(self, user_id: str, limit: int = 5) -> List[UserCategoryHistory]:
        """Get user's most played categories"""
        response = (
            self.client
            .table(self.category_history_table)
            .select("*")
            .eq("user_id", user_id)
            .order("play_count", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [UserCategoryHistory.from_dict(data) for data in response.data]
    
    async def get_recent_categories(self, user_id: str, days: int = 30, limit: int = 5) -> List[UserCategoryHistory]:
        """Get categories played recently by the user"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = (
            self.client
            .table(self.category_history_table)
            .select("*")
            .eq("user_id", user_id)
            .gt("last_played_at", cutoff_date)
            .order("last_played_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        return [UserCategoryHistory.from_dict(data) for data in response.data]