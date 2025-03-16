#!/usr/bin/env python
import os
import sys
import importlib

# Define the src path
src_path = "/Users/sanjaybiswas/development/trivia-app/backend/src"
print(f"Adding to sys.path: {src_path}")

# Add src directory to the Python path
sys.path.insert(0, src_path)

# Define modules to import
modules_to_import = [
    "config.environment",
    "config.llm_config",
    "models.question",
    "models.answer",
    "models.complete_question",
    "utils.question_generator.category_helper",
    "utils.question_generator.difficulty_helper",
    "utils.question_generator.generator",
    "utils.question_generator.answer_generator",
    "utils.question_generator.deduplicator"
]

# Try importing each module one by one
for module_name in modules_to_import:
    try:
        module = importlib.import_module(module_name)
        print(f"Successfully imported: {module_name}")
    except ImportError as e:
        print(f"Failed to import: {module_name}")
        print(f"Error: {e}")
        
        # Check if the module file exists
        module_path = module_name.replace(".", "/")
        full_path = os.path.join(src_path, f"{module_path}.py")
        directory_path = os.path.join(src_path, module_path)
        
        print(f"Checking if file exists at: {full_path}")
        print(f"File exists: {os.path.exists(full_path)}")
        
        print(f"Checking if directory exists at: {directory_path}")
        print(f"Directory exists: {os.path.exists(directory_path)}")
        
        if os.path.exists(directory_path):
            print("Files in directory:")
            for file in os.listdir(directory_path):
                print(f"  {file}")