"""
Response validation and normalization schemas.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExplanationSchema:
    """
    Schema for validating and normalizing AI explanation responses.
    
    Ensures that responses from various providers conform to a consistent
    structure with all required fields.
    """

    REQUIRED_FIELDS = {
        "short_translation": str,
        "literal_gloss": str,
        "meaning_in_context": str,
        "grammar_notes": list,
        "alternatives": list,
        "usage_notes": str,
        "confidence": float,
    }

    @staticmethod
    def validate_and_normalize(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize an explanation response.
        
        Args:
            response: Raw response from AI provider
            
        Returns:
            Normalized response with all required fields
            
        Raises:
            ValueError: If response is completely invalid
        """
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")

        normalized = {}

        # Validate and normalize each field
        normalized["short_translation"] = ExplanationSchema._get_string(
            response, "short_translation", ""
        )
        
        normalized["literal_gloss"] = ExplanationSchema._get_string(
            response, "literal_gloss", ""
        )
        
        normalized["meaning_in_context"] = ExplanationSchema._get_string(
            response, "meaning_in_context", ""
        )
        
        normalized["grammar_notes"] = ExplanationSchema._get_list(
            response, "grammar_notes", []
        )
        
        normalized["alternatives"] = ExplanationSchema._get_list(
            response, "alternatives", []
        )
        
        normalized["usage_notes"] = ExplanationSchema._get_string(
            response, "usage_notes", ""
        )
        
        normalized["confidence"] = ExplanationSchema._get_confidence(
            response, "confidence", 0.5
        )

        # Check if we got at least some meaningful content
        has_content = any([
            normalized["short_translation"],
            normalized["literal_gloss"],
            normalized["meaning_in_context"],
            normalized["usage_notes"],
        ])

        if not has_content:
            logger.warning("Response validation: No meaningful content found")
            raise ValueError("Response contains no meaningful content")

        return normalized

    @staticmethod
    def _get_string(data: Dict[str, Any], key: str, default: str) -> str:
        """Get a string value from response, with fallback to default."""
        value = data.get(key, default)
        if not isinstance(value, str):
            logger.warning(f"Expected string for '{key}', got {type(value)}")
            return default
        return value.strip()

    @staticmethod
    def _get_list(data: Dict[str, Any], key: str, default: List) -> List[str]:
        """Get a list value from response, with fallback to default."""
        value = data.get(key, default)
        if not isinstance(value, list):
            logger.warning(f"Expected list for '{key}', got {type(value)}")
            return default
        
        # Ensure all items are strings
        result = []
        for item in value:
            if isinstance(item, str):
                result.append(item.strip())
            else:
                logger.warning(f"Non-string item in '{key}': {type(item)}")
                result.append(str(item))
        
        return result

    @staticmethod
    def _get_confidence(data: Dict[str, Any], key: str, default: float) -> float:
        """Get confidence value, ensuring it's between 0.0 and 1.0."""
        value = data.get(key, default)
        
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            logger.warning(f"Invalid confidence value: {value}, using default")
            return default
        
        # Clamp to [0.0, 1.0]
        if confidence < 0.0:
            return 0.0
        if confidence > 1.0:
            return 1.0
        
        return confidence


def create_error_response(error_message: str) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Human-readable error message
        
    Returns:
        Error response dictionary
    """
    return {
        "short_translation": "",
        "literal_gloss": "",
        "meaning_in_context": f"Error: {error_message}",
        "grammar_notes": [],
        "alternatives": [],
        "usage_notes": "",
        "confidence": 0.0,
    }
