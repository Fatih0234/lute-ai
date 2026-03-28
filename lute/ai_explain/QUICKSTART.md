# MiniMax AI Integration - Quick Start Guide

## Setup

1. **Install dependencies**:
```bash
pip install -e .
```

2. **Set your API key**:
```bash
export ANTHROPIC_API_KEY=your_minimax_api_key_here
```

3. **Start Lute**:
```bash
python3 -m lute.main
```

You should see:
```
AI explanation service: Enabled
  * Provider: MiniMax (MiniMax-M2.7)
```

## Testing the API

### Check if service is available:
```bash
curl http://localhost:5000/api/explain/status
```

### Request an explanation:
```bash
curl -X POST http://localhost:5000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Eines Tages sagte Lina zu ihrem Vater",
    "source_language": "German",
    "target_language": "English"
  }'
```

### Example Response:
```json
{
  "success": true,
  "explanation": {
    "short_translation": "One day, Lina said to her father",
    "literal_gloss": "One-of days said Lina to her-the father",
    "meaning_in_context": "This phrase introduces a narrative event...",
    "grammar_notes": [
      "Eines Tages - genitive construction meaning 'one day'",
      "sagte - simple past of sagen (to say)",
      "zu + dative - 'to' indicating direction/recipient"
    ],
    "alternatives": ["An einem Tag", "Einmal"],
    "usage_notes": "Commonly used to begin stories or anecdotes in German. Creates a narrative distance.",
    "confidence": 0.95
  }
}
```

## Environment Variables

- `ANTHROPIC_API_KEY` (required): Your MiniMax API key
- `ANTHROPIC_BASE_URL` (optional): Default is `https://api.minimax.io/anthropic`
- `ANTHROPIC_MODEL` (optional): Default is `MiniMax-M2.7`
- `AI_REQUEST_TIMEOUT` (optional): Default is `30` seconds

## Error Handling

### Missing API Key (500):
```json
{
  "success": false,
  "error": "AI explanation feature is not configured. Please set the ANTHROPIC_API_KEY environment variable..."
}
```

### Invalid Request (400):
```json
{
  "success": false,
  "error": "Missing required parameter: text"
}
```

### Provider Failure (503):
```json
{
  "success": false,
  "error": "AI service error: Request timeout"
}
```

## Verification Tests

Run these commands to verify the installation:

```bash
# Test config
python3 -c "from lute.ai_explain.config import AIConfig; import os; os.environ['ANTHROPIC_API_KEY']='test'; c=AIConfig(); assert c.is_configured(); print('✅ Config OK')"

# Test schemas
python3 -c "from lute.ai_explain.schemas import ExplanationSchema; r={'short_translation':'Test','meaning_in_context':'Test'}; ExplanationSchema.validate_and_normalize(r); print('✅ Schema validation OK')"

# Test provider initialization (requires valid API key)
python3 -c "from lute.ai_explain.providers.minimax_provider import MiniMaxProvider; p=MiniMaxProvider(); print(f'✅ Provider available: {p.is_available()}')"
```

## Next Steps

The backend is complete and ready for frontend integration. You can:

1. Call the `/api/explain` endpoint from your JavaScript/frontend code
2. Display the structured explanation to users
3. Add UI for switching explanation language (like Readlang's "Switch explanations to English")

See `lute/ai_explain/README.md` for full documentation.
