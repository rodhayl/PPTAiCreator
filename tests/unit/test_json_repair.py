"""Test JSON repair utility."""

from src.utils import parse_json_with_repair


def test_json_repair_returns_raw_on_failure():
    # Test that parse_json_with_repair handles invalid JSON gracefully
    invalid_json = "this is not valid json at all"

    # Should return the raw string when JSON parsing fails
    result = parse_json_with_repair(invalid_json)
    assert isinstance(result, str)
    assert result == invalid_json


def test_json_repair_extracts_valid_json():
    # Test that parse_json_with_repair can extract JSON from surrounding text
    text_with_json = 'Here is the result: {"key": "value", "number": 42}'

    result = parse_json_with_repair(text_with_json)
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_json_repair_handles_valid_json():
    # Test that parse_json_with_repair passes through valid JSON
    valid_json = '{"test": true, "count": 100}'

    result = parse_json_with_repair(valid_json)
    assert isinstance(result, dict)
    assert result["test"] is True
    assert result["count"] == 100
