# backend/src/utils/llm/__init__.py
"""
LLM service module for interacting with Language Model APIs.

This package provides services and utilities for working with
various LLM providers (OpenAI, Anthropic, Gemini) and processing
their outputs.
"""

from .llm_service import LLMService
from .llm_parsing_utils import (
    LLMParsingUtils,
    extract_bullet_list,
    parse_json_from_llm,
    format_as_bullet_list,
    extract_key_value_pairs,
    detect_and_parse_format
)
from .llm_json_repair import (
    LLMJsonRepair,
    repair_json,
    repair_and_parse
)

__all__ = [
    "LLMService",
    "LLMParsingUtils",
    "extract_bullet_list",
    "parse_json_from_llm",
    "format_as_bullet_list",
    "extract_key_value_pairs",
    "detect_and_parse_format",
    "LLMJsonRepair",
    "repair_json",
    "repair_and_parse",
]