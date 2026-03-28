"""
MiniMax provider using Anthropic-compatible API.
"""

import json
import logging
from typing import Dict, Any

try:
    from anthropic import Anthropic, AnthropicError

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from lute.ai_explain.providers.base import ExplanationProvider
from lute.ai_explain.config import get_config

logger = logging.getLogger(__name__)


class MiniMaxProvider(ExplanationProvider):
    """
    MiniMax provider using Anthropic-compatible API endpoint.

    Connects to MiniMax's API using the Anthropic SDK with a custom base URL.
    """

    def __init__(self):
        """Initialize the MiniMax provider."""
        self.config = get_config()
        self.client = None

        if ANTHROPIC_AVAILABLE and self.config.is_configured():
            try:
                self.client = Anthropic(
                    api_key=self.config.anthropic_api_key,
                    base_url=self.config.anthropic_base_url,
                    timeout=self.config.request_timeout,
                )
                logger.info(
                    f"MiniMax provider initialized with base URL: "
                    f"{self.config.anthropic_base_url}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize MiniMax client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Check if the provider is available."""
        if not ANTHROPIC_AVAILABLE:
            return False
        if not self.config.is_configured():
            return False
        return self.client is not None

    def get_unavailable_reason(self) -> str:
        """Get reason why provider is unavailable."""
        if not ANTHROPIC_AVAILABLE:
            return (
                "Anthropic SDK is not installed. "
                "Please install it with: pip install anthropic"
            )
        if not self.config.is_configured():
            return self.config.get_config_error_message()
        if self.client is None:
            return "MiniMax client failed to initialize. Check your API key and configuration."
        return "Unknown error"

    def explain(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Dict[str, Any]:
        """
        Generate an explanation using MiniMax (synchronous).

        Args:
            text: Text to explain
            source_language: Source language name
            target_language: Target language name

        Returns:
            Structured explanation dictionary

        Raises:
            RuntimeError: If provider is not available or API call fails
        """
        if not self.is_available():
            raise RuntimeError(self.get_unavailable_reason())

        prompt = self._build_prompt(text, source_language, target_language)

        try:
            logger.info(f"Requesting explanation from MiniMax for: {text[:50]}...")

            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract the text content from the response
            if not response.content or len(response.content) == 0:
                raise RuntimeError("Empty response from MiniMax")

            # Handle different content block types (TextBlock, ThinkingBlock, etc.)
            response_text = None
            for block in response.content:
                if hasattr(block, "text"):
                    response_text = block.text
                    break
                elif hasattr(block, "type") and block.type == "text":
                    response_text = block.text
                    break

            if not response_text:
                logger.error(
                    f"Could not extract text from response content: {response.content}"
                )
                raise RuntimeError(
                    f"No text content in response. Content types: {[type(b).__name__ for b in response.content]}"
                )

            logger.debug(f"Raw MiniMax response: {response_text[:200]}...")

            # Return the markdown text directly (no JSON parsing)
            logger.info("Successfully received explanation from MiniMax")
            return response_text

        except AnthropicError as e:
            logger.error(f"MiniMax API error: {e}")
            raise RuntimeError(f"MiniMax API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling MiniMax: {e}")
            raise RuntimeError(f"Failed to get explanation: {str(e)}")

    def explain_stream(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ):
        """
        Generate an explanation using MiniMax (streaming).

        Yields text chunks as they arrive from the API.

        Args:
            text: Text to explain
            source_language: Source language name
            target_language: Target language name

        Yields:
            String chunks of the markdown response

        Raises:
            RuntimeError: If provider is not available or API call fails
        """
        if not self.is_available():
            raise RuntimeError(self.get_unavailable_reason())

        prompt = self._build_prompt(text, source_language, target_language)

        try:
            logger.info(
                f"Starting streaming explanation from MiniMax for: {text[:50]}..."
            )

            with self.client.messages.stream(
                model=self.config.model_name,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text_chunk in stream.text_stream:
                    yield text_chunk

            logger.info("Streaming explanation completed from MiniMax")

        except AnthropicError as e:
            logger.error(f"MiniMax streaming API error: {e}")
            raise RuntimeError(f"MiniMax API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in MiniMax streaming: {e}")
            raise RuntimeError(f"Failed to stream explanation: {str(e)}")

    def _build_prompt(
        self, text: str, source_language: str, target_language: str
    ) -> str:
        """
        Build a prompt for MiniMax that generates markdown.

        Args:
            text: Text to explain
            source_language: Source language
            target_language: Target language

        Returns:
            Formatted prompt string
        """
        return f"""You are a language learning assistant helping someone learn {source_language}.

Text to explain: "{text}"

Your response MUST be written entirely in {target_language} (the target language), except for the English translation in the header.

Provide your explanation in markdown format with this exact structure, but translate ALL the section headers (marked with ##) into {target_language}:

# "{text}" — [Write the actual English translation here, NOT placeholder text]

A brief sentence in {target_language} explaining what this phrase means.

## [Translate "Usual Meaning" into {target_language}]

Explain in {target_language} what this phrase means in a general context. Describe the typical usage, implications, and when it's commonly used. Be concise but informative. All text must be in {target_language}.

## [Translate "Meaning in Context" into {target_language}]

Explain in {target_language} what this phrase means specifically in the given narrative/story context. How does it function here? What does it suggest about the situation or characters? All text must be in {target_language}.

## [Translate "Grammar Notes" into {target_language}] (Optional)

If relevant, add 2-3 brief bullet points in {target_language} about:
- Key grammar structures used
- Word order or tense
- Important grammatical features

## [Translate "Alternatives" into {target_language}] (Optional)

If there are other ways to express the same idea in {source_language}, list them in {target_language}.

CRITICAL INSTRUCTIONS:
1. The header MUST start with the original {source_language} text: "{text}"
2. Then a dash (—) 
3. Then the ACTUAL English translation of "{text}" - do NOT write placeholder text like "[English translation]", instead provide the real translation like "beats the kettledrums" or "plays the drums"
4. This header format is the ONLY place where English can appear - everywhere else must be in {target_language}
5. Even when explaining in English, use this same header format with the original text first

Every single word in your response must be in {target_language}, including all section headers, except for the English translation in the # header.

Keep your response concise, learner-friendly, and well-formatted in markdown. Use **bold** for emphasis where helpful."""
