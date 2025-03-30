# backend/src/utils/question_generation/text_utils.py
"""
Text utilities specifically for trivia question generation.
Leverages the document_processing utilities.
"""

import re
from typing import List
from ..document_processing.processors import clean_text, split_into_chunks
from ..llm.llm_parsing_utils import extract_bullet_list, format_as_bullet_list

def clean_trivia_text(text: str, remove_citations: bool = True) -> str:
    """
    Clean text specifically for trivia question content.
    
    Args:
        text: The input text to clean
        remove_citations: Whether to remove citation markers like [1], [2], etc.
        
    Returns:
        Cleaned text suitable for trivia
    """
    # Use clean_text from document_processing
    cleaned = clean_text(text, remove_extra_whitespace=True)
    
    # Additional cleaning specific to trivia content
    if remove_citations:
        # Remove citation markers like [1], [2], etc.
        cleaned = re.sub(r'\[\d+\]', '', cleaned)
    
    return cleaned

def chunk_trivia_content(content: str, difficulty: str) -> List[str]:
    """
    Split trivia content into appropriate chunks based on difficulty.
    
    Args:
        content: The content to split
        difficulty: Difficulty level affecting chunk size
        
    Returns:
        List of content chunks
    """
    # Adjust chunk size based on difficulty
    if difficulty.lower() == "easy":
        chunk_size = 800  # Smaller chunks for easy questions
    elif difficulty.lower() == "medium":
        chunk_size = 1200
    else:  # Hard or Expert
        chunk_size = 1600  # Larger chunks for hard/expert questions
    
    # Use split_into_chunks from document_processing
    return split_into_chunks(content, chunk_size=chunk_size, respect_sentences=True)