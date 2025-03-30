#!/usr/bin/env python3
# backend/test_supabase_integration.py

import os
import sys
import uuid
import asyncio
import unittest
from datetime import datetime
from typing import List, Optional

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import configuration and Supabase client
from config.config import SupabaseConfig
from supabase_py_async import create_client

# Import models
from models.pack import Pack, PackCreate, PackUpdate, CreatorType
from models.pack_group import PackGroup, PackGroupCreate
from models.question import Question, QuestionCreate, DifficultyLevel
from models.incorrect_answers import IncorrectAnswers, IncorrectAnswersCreate

# Import repositories
from repositories.pack_repository import PackRepository
from repositories.pack_group_repository import PackGroupRepository
from repositories.question_repository import QuestionRepository
from repositories.incorrect_answers_repository import IncorrectAnswersRepository

class TestSupabaseIntegration:
    """Integration test for Supabase database operations."""
    
    def __init__(self):
        self.test_ids = []  # Store IDs of test records for cleanup
        self.supabase = None
        self.pack_repo = None
        self.pack_group_repo = None
        self.question_repo = None
        self.incorrect_answers_repo = None
    
    async def setup(self):
        """Set up Supabase connection and repositories."""
        print("Setting up Supabase connection...")
        
        # Load configuration
        supabase_config = SupabaseConfig()
        url = supabase_config.get_supabase_url()
        key = supabase_config.get_supabase_key()
        
        if not url or not key:
            print("ERROR: Supabase URL or key not found in environment variables.")
            print("Make sure to set SUPABASE_URL and SUPABASE_KEY in your .env file.")
            sys.exit(1)
        
        # Initialize Supabase client
        self.supabase = await create_client(url, key)
        
        # Initialize repositories
        self.pack_repo = PackRepository(self.supabase)
        self.pack_group_repo = PackGroupRepository(self.supabase)
        self.question_repo = QuestionRepository(self.supabase)
        self.incorrect_answers_repo = IncorrectAnswersRepository(self.supabase)
        
        print("Setup complete.")
    
    async def test_pack_group_operations(self):
        """Test PackGroup CRUD operations."""
        print("\n--- Testing PackGroup Operations ---")
        
        # Create a pack group
        group_name = f"Test Group {uuid.uuid4()}"
        group_create = PackGroupCreate(name=group_name)
        
        print(f"Creating pack group: {group_name}")
        pack_group = await self.pack_group_repo.create(obj_in=group_create)
        self.test_ids.append(("pack_groups", pack_group.id))
        
        print(f"Created pack group with ID: {pack_group.id}")
        
        # Retrieve the pack group
        retrieved_group = await self.pack_group_repo.get_by_id(pack_group.id)
        assert retrieved_group is not None, "Failed to retrieve pack group"
        assert retrieved_group.name == group_name, "Retrieved group name does not match"
        print("Successfully retrieved pack group")
        
        # Test get_by_name
        found_group = await self.pack_group_repo.get_by_name(group_name)
        assert found_group is not None, "Failed to retrieve pack group by name"
        assert found_group.id == pack_group.id, "Retrieved group ID does not match"
        print("Successfully retrieved pack group by name")
        
        return pack_group
    
    async def test_pack_operations(self, pack_group: Optional[PackGroup] = None):
        """Test Pack CRUD operations."""
        print("\n--- Testing Pack Operations ---")
        
        # Create a pack
        pack_name = f"Test Pack {uuid.uuid4()}"
        pack_create = PackCreate(
            name=pack_name,
            description="A test pack for integration testing",
            price=0.0,
            creator_type=CreatorType.SYSTEM,
            pack_group_id=[pack_group.id] if pack_group else None
        )
        
        print(f"Creating pack: {pack_name}")
        pack = await self.pack_repo.create(obj_in=pack_create)
        self.test_ids.append(("packs", pack.id))
        
        print(f"Created pack with ID: {pack.id}")
        
        # Retrieve the pack
        retrieved_pack = await self.pack_repo.get_by_id(pack.id)
        assert retrieved_pack is not None, "Failed to retrieve pack"
        assert retrieved_pack.name == pack_name, "Retrieved pack name does not match"
        print("Successfully retrieved pack")
        
        # Update the pack
        updated_description = "Updated description for testing"
        pack_update = PackUpdate(description=updated_description)
        
        updated_pack = await self.pack_repo.update(id=pack.id, obj_in=pack_update)
        assert updated_pack is not None, "Failed to update pack"
        assert updated_pack.description == updated_description, "Pack description not updated"
        print("Successfully updated pack")
        
        # Test get_by_pack_group_id if we have a pack group
        if pack_group:
            packs_by_group = await self.pack_repo.get_by_pack_group_id(pack_group.id)
            assert len(packs_by_group) > 0, "Failed to retrieve packs by group ID"
            assert any(p.id == pack.id for p in packs_by_group), "Pack not found in group packs"
            print("Successfully retrieved packs by pack group ID")
        
        # Test search_by_name
        found_packs = await self.pack_repo.search_by_name(pack_name.split()[-1])  # Search by last part of name
        assert len(found_packs) > 0, "Failed to search packs by name"
        assert any(p.id == pack.id for p in found_packs), "Pack not found in search results"
        print("Successfully searched packs by name")
        
        return pack
    
    async def test_question_and_answers_operations(self, pack: Pack):
        """Test Question and IncorrectAnswers CRUD operations."""
        print("\n--- Testing Question and IncorrectAnswers Operations ---")
        
        # Create a question
        question_text = f"What is the test question {uuid.uuid4()}?"
        question_create = QuestionCreate(
            question=question_text,
            answer="This is the test answer",
            pack_id=pack.id,
            difficulty_initial=DifficultyLevel.MEDIUM
        )
        
        print(f"Creating question: {question_text}")
        question = await self.question_repo.create(obj_in=question_create)
        self.test_ids.append(("questions", question.id))
        
        print(f"Created question with ID: {question.id}")
        
        # Retrieve the question
        retrieved_question = await self.question_repo.get_by_id(question.id)
        assert retrieved_question is not None, "Failed to retrieve question"
        assert retrieved_question.question == question_text, "Retrieved question text does not match"
        print("Successfully retrieved question")
        
        # Test get_by_pack_id
        questions_by_pack = await self.question_repo.get_by_pack_id(pack.id)
        assert len(questions_by_pack) > 0, "Failed to retrieve questions by pack ID"
        assert any(q.id == question.id for q in questions_by_pack), "Question not found in pack questions"
        print("Successfully retrieved questions by pack ID")
        
        # Create incorrect answers
        incorrect_answers = ["Wrong answer 1", "Wrong answer 2", "Wrong answer 3"]
        incorrect_answers_create = IncorrectAnswersCreate(
            incorrect_answers=incorrect_answers,
            question_id=question.id
        )
        
        print("Creating incorrect answers")
        answers = await self.incorrect_answers_repo.create(obj_in=incorrect_answers_create)
        self.test_ids.append(("incorrect_answers", answers.id))
        
        print(f"Created incorrect answers with ID: {answers.id}")
        
        # Retrieve the incorrect answers
        retrieved_answers = await self.incorrect_answers_repo.get_by_question_id(question.id)
        assert retrieved_answers is not None, "Failed to retrieve incorrect answers"
        assert retrieved_answers.incorrect_answers == incorrect_answers, "Retrieved incorrect answers do not match"
        print("Successfully retrieved incorrect answers by question ID")
        
        return question, answers
    
    async def test_update_statistics(self, question: Question, pack: Pack):
        """Test updating statistics for questions and packs."""
        print("\n--- Testing Statistic Updates ---")
        
        # Update question correct answer rate
        correct_rate = 0.85
        updated_question = await self.question_repo.update_statistics(
            question_id=question.id,
            correct_rate=correct_rate,
            new_difficulty=DifficultyLevel.HARD
        )
        
        assert updated_question is not None, "Failed to update question statistics"
        assert updated_question.correct_answer_rate == correct_rate, "Question correct answer rate not updated"
        assert updated_question.difficulty_current == DifficultyLevel.HARD, "Question difficulty not updated"
        print("Successfully updated question statistics")
        
        # Update pack correct answer rate
        pack_rate = 0.75
        updated_pack = await self.pack_repo.update_correct_answer_rate(
            pack_id=pack.id,
            rate=pack_rate
        )
        
        assert updated_pack is not None, "Failed to update pack statistics"
        assert updated_pack.correct_answer_rate == pack_rate, "Pack correct answer rate not updated"
        print("Successfully updated pack statistics")
    
    async def cleanup(self):
        """Clean up test data by deleting records."""
        print("\n--- Cleaning Up Test Data ---")
        
        # Reverse the order to handle dependencies (delete children before parents)
        for table, id in reversed(self.test_ids):
            try:
                print(f"Deleting from {table}: {id}")
                
                # Use the appropriate repository based on table name
                if table == "pack_groups":
                    await self.pack_group_repo.delete(id=id)
                elif table == "packs":
                    await self.pack_repo.delete(id=id)
                elif table == "questions":
                    await self.question_repo.delete(id=id)
                elif table == "incorrect_answers":
                    await self.incorrect_answers_repo.delete(id=id)
                
            except Exception as e:
                print(f"Error deleting {id} from {table}: {str(e)}")
        
        print("Cleanup complete")
    
    async def run_tests(self):
        """Run all the integration tests."""
        try:
            await self.setup()
            
            # Test PackGroup operations
            pack_group = await self.test_pack_group_operations()
            
            # Test Pack operations
            pack = await self.test_pack_operations(pack_group)
            
            # Test Question and IncorrectAnswers operations
            question, answers = await self.test_question_and_answers_operations(pack)
            
            # Test updating statistics
            await self.test_update_statistics(question, pack)
            
            print("\n✅ All tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()


if __name__ == "__main__":
    tester = TestSupabaseIntegration()
    asyncio.run(tester.run_tests())