"""
Business logic for AI explanation service.

Coordinates between providers and validation layers.
"""

import logging
import time
from typing import Dict, Any, Optional

from lute.ai_explain.providers.minimax_provider import MiniMaxProvider
from lute.ai_explain.schemas import ExplanationSchema, create_error_response

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Service for generating AI-powered text explanations.

    Coordinates between AI providers and response validation.
    """

    def __init__(self, session):
        """
        Initialize the explanation service.

        Args:
            session: SQLAlchemy database session for potential future logging
        """
        self.session = session
        self.provider = MiniMaxProvider()

    def explain_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
        book_id: Optional[int] = None,
        page_num: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate an explanation for the given text.

        Args:
            text: The text to explain
            source_language: Language of the source text (e.g., "German")
            target_language: Language for the explanation (e.g., "English")
            book_id: Optional book ID for context
            page_num: Optional page number for context

        Returns:
            Dictionary containing the explanation with all required fields

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If AI provider is not configured or fails
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValueError("Text is required")
        if not source_language or not source_language.strip():
            raise ValueError("Source language is required")
        if not target_language or not target_language.strip():
            raise ValueError("Target language is required")

        logger.info(
            f"Explanation requested for: '{text[:50]}...' "
            f"({source_language} -> {target_language})"
        )

        # Check if provider is available
        if not self.provider.is_available():
            error_msg = self.provider.get_unavailable_reason()
            logger.error(f"Provider not available: {error_msg}")
            raise RuntimeError(error_msg)

        # Call provider and measure time
        start_time = time.time()

        try:
            raw_response = self.provider.explain(
                text=text.strip(),
                source_language=source_language.strip(),
                target_language=target_language.strip(),
            )

            elapsed = time.time() - start_time
            logger.info(f"Provider response received in {elapsed:.2f}s")

            # Return the markdown text directly
            return raw_response

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Provider failed after {elapsed:.2f}s: {e}")
            raise RuntimeError(f"Failed to get explanation: {str(e)}")

    def explain_text_stream(
        self,
        text: str,
        source_language: str,
        target_language: str,
        book_id: Optional[int] = None,
        page_num: Optional[int] = None,
    ):
        """
        Generate a streaming explanation for the given text.

        Yields text chunks as they arrive from the AI provider.

        Args:
            text: The text to explain
            source_language: Language of the source text (e.g., "German")
            target_language: Language for the explanation (e.g., "English")
            book_id: Optional book ID for context
            page_num: Optional page number for context

        Yields:
            String chunks of the markdown response

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If AI provider is not configured or fails
        """
        # Validate inputs
        if not text or not text.strip():
            raise ValueError("Text is required")
        if not source_language or not source_language.strip():
            raise ValueError("Source language is required")
        if not target_language or not target_language.strip():
            raise ValueError("Target language is required")

        logger.info(
            f"Streaming explanation requested for: '{text[:50]}...' "
            f"({source_language} -> {target_language})"
        )

        # Check if provider is available
        if not self.provider.is_available():
            error_msg = self.provider.get_unavailable_reason()
            logger.error(f"Provider not available: {error_msg}")
            raise RuntimeError(error_msg)

        # Start streaming
        start_time = time.time()

        try:
            for chunk in self.provider.explain_stream(
                text=text.strip(),
                source_language=source_language.strip(),
                target_language=target_language.strip(),
            ):
                yield chunk

            elapsed = time.time() - start_time
            logger.info(f"Streaming completed in {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Streaming failed after {elapsed:.2f}s: {e}")
            raise RuntimeError(f"Failed to stream explanation: {str(e)}")
