# backend/src/utils/document_processing/processors.py
"""
Document content processing utilities.

This module provides functions for cleaning, normalizing, and processing
text extracted from documents.
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
logger = logging.getLogger(__name__)

def clean_text(text: str, 
              remove_extra_whitespace: bool = True,
              remove_urls: bool = False,
              remove_emails: bool = False,
              remove_special_chars: bool = False) -> str:
    """
    Clean text by removing unwanted elements.
    
    Args:
        text: Input text to clean
        remove_extra_whitespace: Whether to collapse multiple whitespaces
        remove_urls: Whether to remove URLs
        remove_emails: Whether to remove email addresses
        remove_special_chars: Whether to remove special characters
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove URLs if requested
    if remove_urls:
        text = re.sub(r'https?://\S+', '', text)
    
    # Remove emails if requested
    if remove_emails:
        text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters if requested
    if remove_special_chars:
        text = re.sub(r'[^\w\s]', '', text)
    
    # Remove extra whitespace if requested
    if remove_extra_whitespace:
        # Replace newlines, tabs, and multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Trim leading/trailing whitespace
        text = text.strip()
    
    return text

def normalize_text(text: str,
                  lowercase: bool = True,
                  remove_accents: bool = False,
                  normalize_whitespace: bool = True) -> str:
    """
    Normalize text for consistent processing.
    
    Args:
        text: Input text to normalize
        lowercase: Whether to convert to lowercase
        remove_accents: Whether to remove accents from characters
        normalize_whitespace: Whether to normalize whitespace
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase if requested
    if lowercase:
        text = text.lower()
    
    # Remove accents if requested
    if remove_accents:
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
    
    # Normalize whitespace if requested
    if normalize_whitespace:
        # Replace tabs, newlines, and multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        # Trim leading/trailing whitespace
        text = text.strip()
    
    return text

def split_into_chunks(text: str,
                     chunk_size: int = 1000,
                     overlap: int = 100,
                     respect_sentences: bool = True) -> List[str]:
    """
    Split a long text into smaller overlapping chunks.
    
    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        respect_sentences: Whether to try to break at sentence boundaries
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # If text is shorter than chunk_size, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Calculate end position for this chunk
        end = start + chunk_size
        
        # If we're at the end of the text, just add the final chunk
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # If we should respect sentence boundaries, try to find a sentence end
        if respect_sentences:
            # Look for sentence-ending punctuation followed by space or newline
            sentence_end = -1
            for pattern in [r'\.[\s\n]', r'![\s\n]', r'\?[\s\n]', r'\."\s', r'!"\s', r'\?"\s']:
                matches = list(re.finditer(pattern, text[start:end + overlap]))
                if matches:
                    # Get the position of the last match
                    last_match = matches[-1]
                    # Add 1 to include the punctuation but not the space
                    sentence_end = start + last_match.start() + 1
            
            if sentence_end > start:
                # We found a sentence boundary
                chunks.append(text[start:sentence_end + 1])
                start = sentence_end + 1
                continue
        
        # If we couldn't find a sentence boundary or aren't respecting them,
        # look for the last space within the overlap region
        if end < len(text):
            # Look for the last space in the overlap region
            last_space = text.rfind(' ', end - overlap, end + overlap)
            
            if last_space > start:
                # We found a space to break at
                chunks.append(text[start:last_space])
                start = last_space + 1
                continue
        
        # If we couldn't find a good break point, just break at chunk_size
        chunks.append(text[start:end])
        start = end
    
    return chunks

def detect_language(text: str) -> str:
    """
    Detect the language of a text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        ISO 639-1 language code (2 letters)
        
    Note:
        This is a placeholder. A real implementation would use a language
        detection library like langdetect or a more comprehensive approach.
    """
    # In a real implementation, you would use a language detection library
    # For example:
    # from langdetect import detect