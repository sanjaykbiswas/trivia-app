# backend/src/utils/document_processing/__init__.py
"""
Document processing utilities for handling various file types and extracting information.

This package provides utilities for parsing, extracting, and processing documents
of different formats, such as PDF, CSV, JSON, and plain text files.
"""

from .parsers import parse_document, parse_pdf, parse_csv, parse_json, parse_txt
from .extractors import extract_text, extract_metadata, extract_tables, extract_structured_data
from .processors import clean_text, normalize_text, split_into_chunks, detect_language
from .helpers import get_mime_type, is_supported_format, get_document_stats

__all__ = [
    # Parsers
    "parse_document",
    "parse_pdf",
    "parse_csv", 
    "parse_json",
    "parse_txt",
    
    # Extractors
    "extract_text",
    "extract_metadata",
    "extract_tables",
    "extract_structured_data",
    
    # Processors
    "clean_text",
    "normalize_text", 
    "split_into_chunks",
    "detect_language",
    
    # Helpers
    "get_mime_type",
    "is_supported_format",
    "get_document_stats",
]