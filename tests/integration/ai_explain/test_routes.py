"""
Integration tests for AI explanation API endpoint.
"""

import pytest
import json


def test_explain_endpoint_requires_json(app_context):
    """Test that endpoint requires JSON content type."""
    with app_context[0].test_client() as client:
        response = client.post("/api/explain", data="not json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "JSON" in data["error"]


def test_explain_endpoint_requires_text(app_context):
    """Test that endpoint requires text parameter."""
    with app_context[0].test_client() as client:
        response = client.post(
            "/api/explain",
            json={
                "source_language": "German",
                "target_language": "English"
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "text" in data["error"].lower()


def test_explain_endpoint_requires_source_language(app_context):
    """Test that endpoint requires source_language parameter."""
    with app_context[0].test_client() as client:
        response = client.post(
            "/api/explain",
            json={
                "text": "Hallo",
                "target_language": "English"
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "source_language" in data["error"].lower()


def test_explain_endpoint_requires_target_language(app_context):
    """Test that endpoint requires target_language parameter."""
    with app_context[0].test_client() as client:
        response = client.post(
            "/api/explain",
            json={
                "text": "Hallo",
                "source_language": "German"
            }
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data["success"]
        assert "target_language" in data["error"].lower()


def test_explain_endpoint_returns_error_when_not_configured(app_context, monkeypatch):
    """Test that endpoint returns helpful error when API key not configured."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    
    # Force config reset
    from lute.ai_explain import config
    config.reset_config()
    
    with app_context[0].test_client() as client:
        response = client.post(
            "/api/explain",
            json={
                "text": "Hallo Welt",
                "source_language": "German",
                "target_language": "English"
            }
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert not data["success"]
        assert "not configured" in data["error"].lower()
        assert "ANTHROPIC_API_KEY" in data["error"]


def test_status_endpoint_returns_availability(app_context):
    """Test that status endpoint returns service availability."""
    with app_context[0].test_client() as client:
        response = client.get("/api/explain/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "available" in data
        assert "provider" in data
        assert data["provider"] == "MiniMax"
