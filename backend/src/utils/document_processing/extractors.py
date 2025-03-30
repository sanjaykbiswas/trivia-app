# backend/src/utils/document_processing/extractors.py
"""
Text and metadata extraction utilities for document processing.

This module provides functions for extracting text, tables, and metadata
from parsed documents.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Union

def extract_text(parsed_document: Dict[str, Any]) -> str:
    """
    Extract plain text from a parsed document.
    
    Args:
        parsed_document: Document dictionary from one of the parsers
        
    Returns:
        Extracted text content as a string
    """
    doc_format = parsed_document.get("format", "")
    
    if doc_format == "pdf":
        return parsed_document.get("text", "")
    elif doc_format == "csv":
        # For CSV, we'll join headers and all rows
        headers = parsed_document.get("headers", [])
        rows = parsed_document.get("rows", [])
        
        # Start with headers
        lines = [",".join(headers)]
        
        # Add each row
        for row in rows:
            lines.append(",".join(str(cell) for cell in row))
            
        return "\n".join(lines)
    elif doc_format == "json":
        # For JSON, convert back to string
        import json
        return json.dumps(parsed_document.get("data", {}), indent=2)
    elif doc_format == "txt":
        return parsed_document.get("text", "")
    else:
        # Try to find text in common fields
        for field in ["text", "content", "body"]:
            if field in parsed_document:
                return parsed_document[field]
        
        # If no text found, return empty string
        return ""

def extract_metadata(parsed_document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract metadata from a parsed document.
    
    Args:
        parsed_document: Document dictionary from one of the parsers
        
    Returns:
        Dictionary of metadata fields
    """
    # Start with an empty metadata dict
    metadata = {}
    
    # Add format information
    metadata["format"] = parsed_document.get("format", "unknown")
    
    # Add document-specific metadata
    if "metadata" in parsed_document:
        metadata.update(parsed_document["metadata"])
    
    # Add size information if available
    if "size" in parsed_document:
        metadata["size"] = parsed_document["size"]
    
    # Add structure information based on format
    doc_format = parsed_document.get("format", "")
    
    if doc_format == "pdf":
        metadata["page_count"] = len(parsed_document.get("pages", []))
    elif doc_format == "csv":
        metadata["row_count"] = len(parsed_document.get("rows", []))
        metadata["column_count"] = len(parsed_document.get("headers", []))
    elif doc_format == "json":
        # Try to determine if it's an object or array
        data = parsed_document.get("data", {})
        if isinstance(data, list):
            metadata["item_count"] = len(data)
            metadata["structure"] = "array"
        else:
            metadata["key_count"] = len(data.keys()) if hasattr(data, "keys") else 0
            metadata["structure"] = "object"
    
    return metadata

def extract_tables(parsed_document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tables from a parsed document.
    
    Args:
        parsed_document: Document dictionary from one of the parsers
        
    Returns:
        List of tables, where each table is a dictionary with headers and rows
    """
    doc_format = parsed_document.get("format", "")
    tables = []
    
    if doc_format == "csv":
        # For CSV, we already have a table structure
        tables.append({
            "headers": parsed_document.get("headers", []),
            "rows": parsed_document.get("rows", []),
            "data": parsed_document.get("data", [])
        })
    elif doc_format == "pdf":
        # In a real implementation, you would extract tables from the PDF
        # using a library like tabula-py, camelot, or pdfplumber
        # This is just a placeholder
        pass
    elif doc_format == "json":
        # Try to detect array of objects as a table
        data = parsed_document.get("data", {})
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # Get all unique keys as headers
            headers = set()
            for item in data:
                if isinstance(item, dict):
                    headers.update(item.keys())
            
            headers = sorted(list(headers))
            
            # Create rows
            rows = []
            for item in data:
                if isinstance(item, dict):
                    row = [item.get(header, "") for header in headers]
                    rows.append(row)
            
            if headers and rows:
                tables.append({
                    "headers": headers,
                    "rows": rows,
                    "data": data
                })
    
    return tables

def extract_structured_data(parsed_document: Dict[str, Any], 
                           patterns: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Extract structured data from document text using patterns.
    
    Args:
        parsed_document: Document dictionary from one of the parsers
        patterns: Dictionary of field names and regex patterns
        
    Returns:
        Dictionary of extracted structured data
    """
    # Default patterns for common fields if none provided
    if not patterns:
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
        }
    
    # Get text from document
    text = extract_text(parsed_document)
    
    # Extract data using patterns
    extracted_data = {}
    for field_name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # For most fields, we'll just take all matches
            extracted_data[field_name] = matches
    
    return extracted_data