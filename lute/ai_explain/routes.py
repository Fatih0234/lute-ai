"""
Flask routes for AI explanation endpoints.
"""

import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
from lute.db import db
from lute.ai_explain.service import ExplanationService
from lute.ai_explain.config import get_config

logger = logging.getLogger(__name__)

bp = Blueprint("ai_explain", __name__, url_prefix="/api")


@bp.route("/explain", methods=["POST"])
def explain():
    """
    Generate an AI explanation for selected text.

    Request JSON:
    {
        "text": "Eines Tages sagte Lina zu ihrem Vater",
        "source_language": "German",
        "target_language": "English",
        "book_id": 123,  # Optional
        "page_num": 5     # Optional
    }

    Response JSON (Success - 200):
    {
        "success": true,
        "explanation": {
            "short_translation": "One day, Lina said to her father",
            "literal_gloss": "One-of days said Lina to her-the father",
            "meaning_in_context": "This phrase introduces a narrative...",
            "grammar_notes": ["Eines Tages is a genitive construction...", ...],
            "alternatives": ["An einem Tag", "Einmal"],
            "usage_notes": "Commonly used to begin stories...",
            "confidence": 0.95
        }
    }

    Error Responses:
    - 400: Missing/invalid parameters
    - 500: AI provider not configured
    - 503: AI provider failed
    """
    # Parse request JSON
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.get_json()

    # Extract required parameters
    text = data.get("text", "").strip()
    source_language = data.get("source_language", "").strip()
    target_language = data.get("target_language", "").strip()

    # Optional parameters
    book_id = data.get("book_id")
    page_num = data.get("page_num")

    # Validate required parameters
    if not text:
        return jsonify(
            {"success": False, "error": "Missing required parameter: text"}
        ), 400

    if not source_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: source_language"}
        ), 400

    if not target_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: target_language"}
        ), 400

    # Check if AI is configured (log warning on startup, return error on request)
    config = get_config()
    if not config.is_configured():
        error_msg = config.get_config_error_message()
        logger.warning(f"AI explanation requested but not configured: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

    # Call service layer
    service = ExplanationService(db.session)

    try:
        explanation = service.explain_text(
            text=text,
            source_language=source_language,
            target_language=target_language,
            book_id=book_id,
            page_num=page_num,
        )

        return jsonify({"success": True, "explanation": explanation}), 200

    except ValueError as e:
        # Client error (invalid input)
        logger.warning(f"Invalid request: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except RuntimeError as e:
        # Provider error
        logger.error(f"Provider error: {e}")
        return jsonify({"success": False, "error": f"AI service error: {str(e)}"}), 503

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error in explain endpoint: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500


@bp.route("/explain/markdown", methods=["POST"])
def explain_markdown():
    """
    Generate an AI explanation in markdown format.

    Returns the markdown text directly for simple display.

    Request JSON:
    {
        "text": "Eines Tages sagte Lina zu ihrem Vater",
        "source_language": "German",
        "target_language": "English",
        "book_id": 123,  # Optional
        "page_num": 5     # Optional
    }

    Response (200):
    Raw markdown text with the explanation

    Error Responses:
    - 400: Missing/invalid parameters
    - 500: AI provider not configured
    - 503: AI provider failed
    """
    # Parse request JSON
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.get_json()

    # Extract required parameters
    text = data.get("text", "").strip()
    source_language = data.get("source_language", "").strip()
    target_language = data.get("target_language", "").strip()

    # Optional parameters
    book_id = data.get("book_id")
    page_num = data.get("page_num")

    # Validate required parameters
    if not text:
        return jsonify(
            {"success": False, "error": "Missing required parameter: text"}
        ), 400

    if not source_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: source_language"}
        ), 400

    if not target_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: target_language"}
        ), 400

    # Check if AI is configured
    config = get_config()
    if not config.is_configured():
        error_msg = config.get_config_error_message()
        logger.warning(
            f"AI markdown explanation requested but not configured: {error_msg}"
        )
        return jsonify({"success": False, "error": error_msg}), 500

    # Call service layer
    service = ExplanationService(db.session)

    try:
        explanation = service.explain_text(
            text=text,
            source_language=source_language,
            target_language=target_language,
            book_id=book_id,
            page_num=page_num,
        )

        # Return markdown text directly with proper content type
        return Response(explanation, mimetype="text/markdown"), 200

    except ValueError as e:
        # Client error (invalid input)
        logger.warning(f"Invalid request: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    except RuntimeError as e:
        # Provider error
        logger.error(f"Provider error: {e}")
        return jsonify({"success": False, "error": f"AI service error: {str(e)}"}), 503

    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error in markdown endpoint: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred"}), 500


@bp.route("/explain/status", methods=["GET"])
def status():
    """
    Check if the AI explanation service is available.

    Response JSON:
    {
        "available": true,
        "provider": "MiniMax",
        "message": "AI explanation service is ready"
    }
    """
    config = get_config()

    if config.is_configured():
        return jsonify(
            {
                "available": True,
                "provider": "MiniMax",
                "model": config.model_name,
                "message": "AI explanation service is ready",
            }
        ), 200
    else:
        return jsonify(
            {
                "available": False,
                "provider": "MiniMax",
                "message": config.get_config_error_message(),
            }
        ), 200


@bp.route("/explain/stream", methods=["POST"])
def explain_stream():
    """
    Generate a streaming AI explanation for selected text.

    Returns text/event-stream with chunks of the JSON response.

    Request JSON:
    {
        "text": "Eines Tages sagte Lina zu ihrem Vater",
        "source_language": "German",
        "target_language": "English",
        "book_id": 123,  # Optional
        "page_num": 5     # Optional
    }

    Response (SSE text/event-stream):
    data: {"chunk": "{\\"short_translation\\":\\"One day, L..."}\n\n
    data: {"chunk": "ina said to her father\\",..."}\n\n
    ... (more chunks)

    Error Responses:
    - 400: Missing/invalid parameters
    - 500: AI provider not configured
    - 503: AI provider failed
    """
    # Parse request JSON
    if not request.is_json:
        return jsonify({"success": False, "error": "Request must be JSON"}), 400

    data = request.get_json()

    # Extract required parameters
    text = data.get("text", "").strip()
    source_language = data.get("source_language", "").strip()
    target_language = data.get("target_language", "").strip()

    # Optional parameters
    book_id = data.get("book_id")
    page_num = data.get("page_num")

    # Validate required parameters
    if not text:
        return jsonify(
            {"success": False, "error": "Missing required parameter: text"}
        ), 400

    if not source_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: source_language"}
        ), 400

    if not target_language:
        return jsonify(
            {"success": False, "error": "Missing required parameter: target_language"}
        ), 400

    # Check if AI is configured
    config = get_config()
    if not config.is_configured():
        error_msg = config.get_config_error_message()
        logger.warning(f"AI streaming requested but not configured: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

    # Call service layer with streaming
    service = ExplanationService(db.session)

    def generate():
        """Generator function for streaming response."""
        try:
            for chunk in service.explain_text_stream(
                text=text,
                source_language=source_language,
                target_language=target_language,
                book_id=book_id,
                page_num=page_num,
            ):
                # Send each chunk as SSE event
                event_data = json.dumps({"chunk": chunk})
                yield f"data: {event_data}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True})}\n\n"

        except ValueError as e:
            # Client error (invalid input)
            logger.warning(f"Invalid streaming request: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        except RuntimeError as e:
            # Provider error
            logger.error(f"Streaming provider error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error in streaming endpoint: {e}")
            yield f"data: {json.dumps({'error': 'An unexpected error occurred'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )
