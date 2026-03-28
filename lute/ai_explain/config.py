"""
Configuration management for AI explanation providers.

Reads configuration from environment variables following Lute conventions.
"""

import os
from typing import Optional


class AIConfig:
    """Configuration for AI explanation providers."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.anthropic_api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
        self.anthropic_base_url: str = os.environ.get(
            "ANTHROPIC_BASE_URL", "https://api.minimax.io/anthropic"
        )
        self.model_name: str = os.environ.get("ANTHROPIC_MODEL", "MiniMax-M2.7")
        self.request_timeout: int = int(os.environ.get("AI_REQUEST_TIMEOUT", "30"))

    def is_configured(self) -> bool:
        """Check if AI provider is properly configured."""
        return self.anthropic_api_key is not None and len(self.anthropic_api_key) > 0

    def get_config_error_message(self) -> str:
        """Get a user-friendly error message when configuration is missing."""
        if not self.anthropic_api_key:
            return (
                "AI explanation feature is not configured. "
                "Please set the ANTHROPIC_API_KEY environment variable with your MiniMax API key. "
                "Visit https://api.minimax.io to obtain an API key."
            )
        return "AI configuration error."

    def __repr__(self) -> str:
        """String representation masking the API key."""
        key_display = "***configured***" if self.anthropic_api_key else "NOT SET"
        return (
            f"AIConfig(api_key={key_display}, "
            f"base_url={self.anthropic_base_url}, "
            f"model={self.model_name})"
        )


# Global configuration instance
_config: Optional[AIConfig] = None


def get_config() -> AIConfig:
    """Get or create the global AI configuration instance."""
    global _config
    if _config is None:
        _config = AIConfig()
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None
