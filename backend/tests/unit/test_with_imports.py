#!/usr/bin/env python
import os
import sys
import json
from pprint import pprint
from datetime import datetime

# Define the absolute path to the src directory
src_path = "/Users/sanjaybiswas/development/trivia-app/backend/src"
print(f"Adding to sys.path: {src_path}")

# Add src directory to the beginning of sys.path to ensure it takes precedence
sys.path.insert(0, src_path)

# First import all modules (exactly as in the successful test)
from config.environment import Environment
from config.llm_config import LLMConfigFactory
from models.question import Question
from models.answer import Answer
from models.complete_question import CompleteQuestion
from utils.question_generator.category_helper import CategoryHelper
from utils.question_generator.difficulty_helper import DifficultyHelper
from utils.question_generator.generator import QuestionGenerator
from utils.question_generator.answer_generator import AnswerGenerator
from utils.question_generator.deduplicator import Deduplicator

print("All modules imported successfully")

def main():
    # Setup environment
    env = Environment()
    
    # Choose a category for testing
    test_category = "Astronomy"
    
    # Configure LLM clients
    question_config = LLMConfigFactory.create_anthropic("claude-3-7-sonnet-20250219")
    answer_config = LLMConfigFactory.create_openai("gpt-3.5-turbo")
    
    # Create helper instances
    category_helper = CategoryHelper(question_config)
    difficulty_helper = DifficultyHelper(question_config)
    question_generator = QuestionGenerator(question_config)
    answer_generator = AnswerGenerator(answer_config)
    deduplicator = Deduplicator()
    
    # Step 1: Generate category guidelines and display them
    print(f"\n{'='*80}\nGENERATING CATEGORY GUIDELINES FOR: {test_category}\n{'='*80}")
    category_guidelines = category_helper.generate_category_guidelines(test_category)
    print(category_guidelines)
    
    # Step 2: Generate difficulty levels and display them
    print(f"\n{'='*80}\nGENERATING DIFFICULTY LEVELS FOR: {test_category}\n{'='*80}")
    difficulty_tiers = difficulty_helper.generate_difficulty_guidelines(test_category)
    print(json.dumps(difficulty_tiers, indent=2))
    
    # Step 3: Generate questions across all 5 difficulty levels
    print(f"\n{'='*80}\nGENERATING QUESTIONS ACROSS ALL DIFFICULTY LEVELS\n{'='*80}")
    
    # Generate 5 questions at each difficulty level (25 total)
    all_questions = []
    difficulties = ["Easy", "Medium", "Hard", "Expert", "Master"]
    
    for difficulty in difficulties:
        print(f"\nGenerating questions for {difficulty} difficulty...")
        questions = question_generator.generate_questions(test_category, 5, difficulty)
        all_questions.extend(questions)
        
        # Print sample of questions for each difficulty
        for i, q in enumerate(questions):
            print(f"  {i+1}. {q.content}")
    
    # Step 4: Check for and remove duplicates
    print(f"\n{'='*80}\nCHECKING FOR DUPLICATES\n{'='*80}")
    print(f"Total questions before deduplication: {len(all_questions)}")
    
    deduplicated_questions = deduplicator.remove_duplicates(all_questions)
    print(f"Total questions after deduplication: {len(deduplicated_questions)}")
    
    # If there were duplicates, show them
    if len(all_questions) != len(deduplicated_questions):
        duplicate_count = len(all_questions) - len(deduplicated_questions)
        print(f"Found {duplicate_count} duplicate questions.")
    
    # Step 5: Generate answers for the deduplicated questions
    print(f"\n{'='*80}\nGENERATING ANSWERS\n{'='*80}")
    
    # Need to simulate question IDs since we're not saving to the database
    for i, q in enumerate(deduplicated_questions):
        q.id = f"test-question-{i+1}"
    
    answers = answer_generator.generate_answers(deduplicated_questions, test_category)
    
    # Step 6: Create complete questions
    print(f"\n{'='*80}\nCREATING COMPLETE QUESTIONS\n{'='*80}")
    
    complete_questions = []
    answer_map = {a.question_id: a for a in answers}
    
    for question in deduplicated_questions:
        if question.id in answer_map:
            complete_question = CompleteQuestion(
                question=question,
                answer=answer_map[question.id]
            )
            complete_questions.append(complete_question)
    
    # Step 7: Output all complete questions with their details
    print(f"\n{'='*80}\nFINAL COMPLETE QUESTIONS ({len(complete_questions)})\n{'='*80}")
    
    for i, cq in enumerate(complete_questions):
        print(f"\nQuestion {i+1}:")
        print(f"  Content: {cq.content}")
        print(f"  Category: {cq.category}")
        print(f"  Correct Answer: {cq.correct_answer}")
        print(f"  Incorrect Answers: {', '.join(cq.incorrect_answers)}")
        print(f"  Difficulty: {cq.difficulty}")
    
    # Step 8: Output final stats
    print(f"\n{'='*80}\nTEST SUMMARY\n{'='*80}")
    print(f"Category: {test_category}")
    print(f"Initial question count: {len(all_questions)}")
    print(f"Questions after deduplication: {len(deduplicated_questions)}")
    print(f"Final complete questions: {len(complete_questions)}")
    
    # Output distribution by difficulty
    difficulty_counts = {}
    for cq in complete_questions:
        difficulty = cq.difficulty
        if difficulty in difficulty_counts:
            difficulty_counts[difficulty] += 1
        else:
            difficulty_counts[difficulty] = 1
    
    print("\nDifficulty distribution:")
    for diff, count in difficulty_counts.items():
        print(f"  {diff}: {count} questions")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()