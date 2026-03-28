# AI Explanation Module

This module provides AI-powered text explanations for language learners using the MiniMax API through Anthropic's compatibility layer.

## Architecture

```
lute/ai_explain/
├── __init__.py              # Module initialization
├── config.py                # Configuration management
├── routes.py                # Flask API endpoints
├── service.py               # Business logic layer
├── schemas.py               # Response validation/normalization
└── providers/
    ├── __init__.py
    ├── base.py              # Abstract provider interface
    └── minimax_provider.py  # MiniMax implementation
```

## Features

- **Provider Abstraction**: Easily swap AI providers without changing application logic
- **Structured Output**: Consistent JSON format with translation, grammar notes, context, and usage tips
- **Response Validation**: Automatic normalization and validation of AI responses
- **Graceful Error Handling**: User-friendly errors when API keys are missing or calls fail
- **Environment-based Config**: No hardcoded credentials

## Setup

### 1. Install Dependencies

The Anthropic SDK is included in `pyproject.toml`:

```bash
pip install -e .
```

### 2. Configure API Key

Set your MiniMax API key as an environment variable:

```bash
export ANTHROPIC_API_KEY=your_minimax_api_key_here
```

Optional configuration:

```bash
# Override the default base URL (default: https://api.minimax.io/anthropic)
export ANTHROPIC_BASE_URL=https://api.minimax.io/anthropic

# Override the model (default: MiniMax-M2.7)
export ANTHROPIC_MODEL=MiniMax-M2.7

# Override request timeout in seconds (default: 30)
export AI_REQUEST_TIMEOUT=30
```

### 3. Verify Configuration

On startup, Lute will log the AI service status:

```
AI explanation service: Enabled
  * Provider: MiniMax (MiniMax-M2.7)
```

Or if not configured:

```
AI explanation service: Not configured
  * Set ANTHROPIC_API_KEY environment variable to enable
```

## API Usage

### Check Service Status

```bash
curl http://localhost:5000/api/explain/status
```

Response:
```json
{
  "available": true,
  "provider": "MiniMax",
  "model": "MiniMax-M2.7",
  "message": "AI explanation service is ready"
}
```

### Request an Explanation

```bash
curl -X POST http://localhost:5000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Eines Tages sagte Lina zu ihrem Vater",
    "source_language": "German",
    "target_language": "English"
  }'
```

Response:
```json
{
  "success": true,
  "explanation": {
    "short_translation": "One day, Lina said to her father",
    "literal_gloss": "One-of days said Lina to her-the father",
    "meaning_in_context": "This phrase introduces a narrative...",
    "grammar_notes": [
      "Eines Tages is a genitive construction meaning 'one day'",
      "sagte is the simple past of sagen (to say)"
    ],
    "alternatives": ["An einem Tag", "Einmal"],
    "usage_notes": "Commonly used to begin stories or anecdotes",
    "confidence": 0.95
  }
}
```

### Error Responses

**Missing API Key (500)**:
```json
{
  "success": false,
  "error": "AI explanation feature is not configured. Please set the ANTHROPIC_API_KEY..."
}
```

**Missing Parameters (400)**:
```json
{
  "success": false,
  "error": "Missing required parameter: text"
}
```

**Provider Failure (503)**:
```json
{
  "success": false,
  "error": "AI service error: Request timeout"
}
```

## Adding New Providers

To add a new AI provider:

1. Create a new provider class in `providers/` that inherits from `ExplanationProvider`
2. Implement the required methods: `explain()`, `is_available()`, `get_unavailable_reason()`
3. Update `service.py` to instantiate your provider
4. Add any necessary configuration to `config.py`

Example:

```python
# providers/openai_provider.py
from lute.ai_explain.providers.base import ExplanationProvider

class OpenAIProvider(ExplanationProvider):
    def explain(self, text, source_language, target_language):
        # Implementation here
        pass
    
    def is_available(self):
        return os.environ.get("OPENAI_API_KEY") is not None
    
    def get_unavailable_reason(self):
        return "OpenAI API key not configured"
```

## Response Schema

All explanations must include these fields:

- `short_translation` (str): Brief translation to target language
- `literal_gloss` (str): Word-by-word breakdown
- `meaning_in_context` (str): Contextual explanation
- `grammar_notes` (list[str]): Key grammar points
- `alternatives` (list[str]): Alternative phrasings
- `usage_notes` (str): Cultural/usage information
- `confidence` (float): Confidence score 0.0-1.0

The `schemas.py` module validates and normalizes all responses to ensure consistency.

## Limitations

- **Text-only**: v1 does not support image or document inputs
- **MiniMax-specific**: Built for MiniMax's Anthropic-compatible API
- **No caching**: Each request calls the API (consider adding caching in future)
- **No rate limiting**: Consider adding rate limits for production use

## Testing

See `tests/unit/ai_explain/` for unit tests and `tests/integration/ai_explain/` for integration tests.

Run tests with:

```bash
pytest tests/unit/ai_explain/
pytest tests/integration/ai_explain/
```

## Troubleshooting

### "SDK not installed" error
Install the Anthropic SDK: `pip install anthropic`

### "API key not configured" error
Set the environment variable: `export ANTHROPIC_API_KEY=your_key`

### Provider initialization fails
Check that your API key is valid and the base URL is correct

### Timeout errors
Increase the timeout: `export AI_REQUEST_TIMEOUT=60`

## Future Enhancements

- Multiple provider support with automatic fallback
- Response caching to reduce API costs
- Rate limiting per user
- Database logging of requests
- Admin UI for configuration
- Support for conversation context
- Batch explanation requests
