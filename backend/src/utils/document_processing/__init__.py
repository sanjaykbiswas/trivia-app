# backend/src/utils/document_processing/__init__.py
"""
Document processing utilities for handling various file types and extracting information.

This package provides utilities for parsing, extracting, and processing documents
of different formats, such as PDF, CSV, JSON, and plain text files.
"""

from .processors import clean_text, normalize_text, split_into_chunks, detect_language

__all__ = [
    # Processors
    "clean_text",
    "normalize_text", 
    "split_into_chunks",
    "detect_language",
]