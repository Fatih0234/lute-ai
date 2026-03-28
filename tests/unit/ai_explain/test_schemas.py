"""
Unit tests for response schemas and validation.
"""

import pytest
from lute.ai_explain.schemas import ExplanationSchema, create_error_response


class TestExplanationSchema:
    """Test explanation response validation."""

    def test_validate_complete_response(self):
        """Test validation of a complete, valid response."""
        response = {
            "short_translation": "Hello world",
            "literal_gloss": "Hello world",
            "meaning_in_context": "A greeting",
            "grammar_notes": ["Simple present"],
            "alternatives": ["Hi there"],
            "usage_notes": "Informal greeting",
            "confidence": 0.9
        }
        
        result = ExplanationSchema.validate_and_normalize(response)
        
        assert result["short_translation"] == "Hello world"
        assert result["confidence"] == 0.9
        assert isinstance(result["grammar_notes"], list)

    def test_validate_missing_fields_uses_defaults(self):
        """Test that missing fields get default values."""
        response = {
            "short_translation": "Hello",
            "meaning_in_context": "Greeting"
        }
        
        result = ExplanationSchema.validate_and_normalize(response)
        
        assert result["short_translation"] == "Hello"
        assert result["literal_gloss"] == ""
        assert result["grammar_notes"] == []
        assert result["alternatives"] == []
        assert result["confidence"] == 0.5

    def test_validate_invalid_confidence_clamped(self):
        """Test that confidence values are clamped to [0, 1]."""
        response = {
            "short_translation": "Test",
            "meaning_in_context": "Test",
            "confidence": 1.5
        }
        
        result = ExplanationSchema.validate_and_normalize(response)
        assert result["confidence"] == 1.0
        
        response["confidence"] = -0.5
        result = ExplanationSchema.validate_and_normalize(response)
        assert result["confidence"] == 0.0

    def test_validate_non_string_fields_converted(self):
        """Test that non-string fields are handled gracefully."""
        response = {
            "short_translation": 123,  # Should be string
            "meaning_in_context": "Valid"
        }
        
        result = ExplanationSchema.validate_and_normalize(response)
        assert result["short_translation"] == ""  # Invalid, uses default

    def test_validate_non_list_grammar_notes(self):
        """Test that non-list grammar notes gets default."""
        response = {
            "short_translation": "Test",
            "meaning_in_context": "Test",
            "grammar_notes": "Not a list"
        }
        
        result = ExplanationSchema.validate_and_normalize(response)
        assert result["grammar_notes"] == []

    def test_validate_empty_response_raises_error(self):
        """Test that completely empty response raises error."""
        response = {}
        
        with pytest.raises(ValueError, match="no meaningful content"):
            ExplanationSchema.validate_and_normalize(response)

    def test_validate_non_dict_raises_error(self):
        """Test that non-dict input raises error."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            ExplanationSchema.validate_and_normalize("not a dict")

    def test_create_error_response(self):
        """Test error response creation."""
        error_resp = create_error_response("Test error")
        
        assert error_resp["confidence"] == 0.0
        assert "Test error" in error_resp["meaning_in_context"]
        assert error_resp["short_translation"] == ""
