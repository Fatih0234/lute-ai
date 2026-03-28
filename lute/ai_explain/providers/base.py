"""
Abstract base class for AI explanation providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ExplanationProvider(ABC):
    """
    Abstract base class for AI explanation providers.
    
    Providers implement the explain() method to generate structured
    explanations for text selections in a language learning context.
    """

    @abstractmethod
    def explain(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Dict[str, Any]:
        """
        Generate an explanation for the given text.
        
        Args:
            text: The text to explain (word, phrase, or sentence)
            source_language: Language of the source text (e.g., "German", "Spanish")
            target_language: Language for the explanation (e.g., "English", "French")
            
        Returns:
            Dictionary with the following structure:
            {
                "short_translation": str,      # Brief translation
                "literal_gloss": str,          # Word-by-word breakdown
                "meaning_in_context": str,     # Contextual meaning explanation
                "grammar_notes": List[str],    # List of grammar points
                "alternatives": List[str],     # Alternative ways to express this
                "usage_notes": str,            # Usage and cultural notes
                "confidence": float            # Confidence score (0.0 to 1.0)
            }
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If the provider fails to generate an explanation
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is properly configured and available.
        
        Returns:
            True if the provider can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_unavailable_reason(self) -> str:
        """
        Get a user-friendly message explaining why the provider is unavailable.
        
        Returns:
            Error message string
        """
        pass
