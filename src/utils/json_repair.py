"""JSON parsing utilities with automatic repair logic.

This module provides utilities for parsing JSON from AI model responses,
with automatic repair when the response contains extra text around the JSON.
"""

from __future__ import annotations

import json
from typing import Union


def parse_json_with_repair(raw: str) -> Union[dict, list, str]:
    """Parse JSON from AI response with automatic repair logic.

    This function attempts to parse JSON and if it fails, tries to repair
    by finding the first and last braces/brackets and extracting the JSON
    content from surrounding text.

    Args:
        raw: Raw text response from AI model that may contain JSON

    Returns:
        Parsed JSON object (dict or list) if successful, or the raw string
        if parsing fails after all repair attempts

    Example:
        >>> result = parse_json_with_repair('Here is the data: {"key": "value"}')
        >>> assert result == {"key": "value"}

        >>> result = parse_json_with_repair('[1, 2, 3] and more text')
        >>> assert result == [1, 2, 3]

        >>> result = parse_json_with_repair('Not JSON at all')
        >>> assert result == 'Not JSON at all'
    """
    # Attempt direct parsing
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try to repair by finding object braces
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    # Try to repair by finding array brackets
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1 and end > start:
        snippet = raw[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            pass

    # Fallback: return the raw string
    return raw
