"""
Unit tests for AI configuration.
"""

import os
import pytest
from lute.ai_explain.config import AIConfig, get_config, reset_config


class TestAIConfig:
    """Test AI configuration management."""

    def setup_method(self):
        """Reset config before each test."""
        reset_config()

    def test_config_not_configured_without_api_key(self, monkeypatch):
        """Test that config is not configured without API key."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        config = AIConfig()
        assert not config.is_configured()
        assert "not configured" in config.get_config_error_message().lower()

    def test_config_is_configured_with_api_key(self, monkeypatch):
        """Test that config is configured with API key."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        
        config = AIConfig()
        assert config.is_configured()

    def test_config_uses_default_base_url(self, monkeypatch):
        """Test that config uses MiniMax base URL by default."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
        
        config = AIConfig()
        assert config.anthropic_base_url == "https://api.minimax.io/anthropic"

    def test_config_allows_custom_base_url(self, monkeypatch):
        """Test that config can use custom base URL."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://custom.url")
        
        config = AIConfig()
        assert config.anthropic_base_url == "https://custom.url"

    def test_config_uses_default_model(self, monkeypatch):
        """Test that config uses MiniMax-M2.7 by default."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        
        config = AIConfig()
        assert config.model_name == "MiniMax-M2.7"

    def test_config_repr_masks_api_key(self, monkeypatch):
        """Test that config repr doesn't expose API key."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "secret-key-123")
        
        config = AIConfig()
        repr_str = repr(config)
        
        assert "secret-key-123" not in repr_str
        assert "***configured***" in repr_str

    def test_get_config_returns_singleton(self, monkeypatch):
        """Test that get_config returns the same instance."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
