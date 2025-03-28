from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from models.user_question_history import UserQuestionHistory
from models.user_category_history import UserCategoryHistory
from repositories.base_repository import BaseRepository
from repositories.category_repository import CategoryRepository

class UserHistoryRepository:
    """
    Repository for managing user history in the database
    """
    def __init__(self, supabase_client, category_repository=None):
        self.client = supabase_client
        self.question_history_table = "user_question_history"
        self.category_history_table = "user_category_history"
        self.category_repository = category_repository
    
    async def get_category_repository(self):
        """
        Lazy initialization of category repository if not provided
        
        Returns:
            CategoryRepository: Repository for category operations
        """
        if not self.category_repository:
            from repositories.category_repository import CategoryRepository
            self.category_repository = CategoryRepository(self.client)
        return self.category_repository
    
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
    
    async def add_category_play(self, user_id: str, category_id: str) -> UserCategoryHistory:
        """
        Add or update category play history
        
        Args:
            user_id (str): User ID
            category_id (str): Category ID
            
        Returns:
            UserCategoryHistory: Updated history record
        """
        # Check if history already exists
        response = (
            self.client
            .table(self.category_history_table)
            .select("*")
            .eq("user_id", user_id)
            .eq("category_id", category_id)
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
                category_id=category_id,
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
    
    async def add_category_play_by_name(self, user_id: str, category_name: str) -> UserCategoryHistory:
        """
        Add or update category play history using category name
        
        Args:
            user_id (str): User ID
            category_name (str): Category name
            
        Returns:
            UserCategoryHistory: Updated history record
        """
        # Look up or create the category
        category_repo = await self.get_category_repository()
        category = await category_repo.get_or_create_by_name(category_name)
        
        # Now add the play with the category ID
        return await self.add_category_play(user_id, category.id)
    
    async def get_user_category_history(self, user_id: str, limit: int = 20) -> List[UserCategoryHistory]:
        """
        Get category history for a user
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of records to return
            
        Returns:
            List[UserCategoryHistory]: User's category history
        """
        response = (
            self.client
            .table(self.category_history_table)
            .select("*, categories(name)")  # Join with categories to get names
            .eq("user_id", user_id)
            .order("last_played_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        history_items = []
        for data in response.data:
            # Extract category name from joined data if available
            if "categories" in data and data["categories"]:
                data["category_name"] = data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in data:
                del data["categories"]
                
            history_items.append(UserCategoryHistory.from_dict(data))
            
        return history_items
    
    async def get_user_favorite_categories(self, user_id: str, limit: int = 5) -> List[UserCategoryHistory]:
        """
        Get user's most played categories
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of records to return
            
        Returns:
            List[UserCategoryHistory]: User's favorite categories
        """
        response = (
            self.client
            .table(self.category_history_table)
            .select("*, categories(name)")  # Join with categories to get names
            .eq("user_id", user_id)
            .order("play_count", desc=True)
            .limit(limit)
            .execute()
        )
        
        history_items = []
        for data in response.data:
            # Extract category name from joined data if available
            if "categories" in data and data["categories"]:
                data["category_name"] = data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in data:
                del data["categories"]
                
            history_items.append(UserCategoryHistory.from_dict(data))
            
        return history_items
    
    async def get_recent_categories(self, user_id: str, days: int = 30, limit: int = 5) -> List[UserCategoryHistory]:
        """
        Get categories played recently by the user
        
        Args:
            user_id (str): User ID
            days (int): Number of days to look back
            limit (int): Maximum number of records to return
            
        Returns:
            List[UserCategoryHistory]: Recently played categories
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = (
            self.client
            .table(self.category_history_table)
            .select("*, categories(name)")  # Join with categories to get names
            .eq("user_id", user_id)
            .gt("last_played_at", cutoff_date)
            .order("last_played_at", desc=True)
            .limit(limit)
            .execute()
        )
        
        history_items = []
        for data in response.data:
            # Extract category name from joined data if available
            if "categories" in data and data["categories"]:
                data["category_name"] = data["categories"]["name"]
            
            # Remove the joined object to avoid dataclass conflicts
            if "categories" in data:
                del data["categories"]
                
            history_items.append(UserCategoryHistory.from_dict(data))
            
        return history_items