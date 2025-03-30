# backend/src/utils/document_processing/helpers.py
"""
Helper functions for document processing.

This module provides utility functions that support the document parsing,
extraction, and processing operations.
"""

import os
import mimetypes
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Initialize mimetypes
mimetypes.init()

def get_mime_type(filename: str) -> Tuple[str, str]:
    """
    Get the MIME type and file extension from a filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Tuple containing (mime_type, file_extension)
    """
    # Get MIME type based on file extension
    mime_type, _ = mimetypes.guess_type(filename)
    
    # Get file extension
    _, file_extension = os.path.splitext(filename)
    if file_extension.startswith('.'):
        file_extension = file_extension[1:]  # Remove leading dot
    
    # Default to application/octet-stream if no MIME type detected
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    return mime_type, file_extension.lower()

def is_supported_format(filename: str) -> bool:
    """
    Check if a file format is supported by the document processing utilities.
    
    Args:
        filename: Name of the file to check
        
    Returns:
        True if the format is supported, False otherwise
    """
    # Get file extension
    _, file_extension = os.path.splitext(filename)
    if file_extension.startswith('.'):
        file_extension = file_extension[1:]  # Remove leading dot
    
    file_extension = file_extension.lower()
    
    # List of supported file extensions
    supported_extensions = [
        'pdf', 'txt', 'csv', 'json', 'md', 'html', 'htm'
    ]
    
    # Check if extension is supported
    return file_extension in supported_extensions

def get_document_stats(parsed_document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get statistics about a parsed document.
    
    Args:
        parsed_document: Document dictionary from one of the parsers
        
    Returns:
        Dictionary containing document statistics
    """
    stats = {
        "format": parsed_document.get("format", "unknown")
    }
    
    # Get document text
    from .extractors import extract_text
    text = extract_text(parsed_document)
    
    # Calculate basic text statistics
    stats["char_count"] = len(text)
    stats["word_count"] = len(text.split())
    stats["line_count"] = len(text.splitlines())
    
    # Format-specific statistics
    doc_format = parsed_document.get("format", "")
    
    if doc_format == "pdf":
        stats["page_count"] = len(parsed_document.get("pages", []))
    elif doc_format == "csv":
        stats["row_count"] = len(parsed_document.get("rows", []))
        stats["column_count"] = len(parsed_document.get("headers", []))
    elif doc_format == "json":
        # Try to determine if it's an object or array
        data = parsed_document.get("data", {})
        if isinstance(data, list):
            stats["item_count"] = len(data)
        else:
            stats["key_count"] = len(data.keys()) if hasattr(data, "keys") else 0
    
    return stats