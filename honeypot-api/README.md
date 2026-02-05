# GUVI Agentic Honey-Pot API (FastAPI)

Production-ready FastAPI service for **GUVI Hackathon Problem Statement 2**:
Agentic Honey-Pot for Scam Detection & Intelligence Extraction.

## Features

- `POST /api/honeypot` with strict request validation.
- `x-api-key` header authentication via environment config.
- Hybrid scam detection:
  - rule-based intent scoring
  - optional OpenAI classifier (`OPENAI_API_KEY`) hook
- Human-like agentic reply generation for multi-turn scam engagement.
- Session memory keyed by `sessionId` with max 40 messages retained.
- Regex-based intelligence extraction:
  - UPI IDs
  - phishing URLs
  - phone numbers
  - bank accounts
  - suspicious keywords
- Mandatory callback integration to GUVI endpoint:
  - finalization policy:
    - turns >= 18 OR
    - turns >= 12 AND at least 2 intelligence items extracted
  - retries callback on subsequent requests until successful.
- Structured logging and health endpoint.

## Folder Structure

```text
honeypot-api/
  app/
    main.py
    config.py
    models.py
    memory_store.py
    scam_detector.py
    agent.py
    extractors.py
    callback_client.py
  requirements.txt
  Dockerfile
  README.md
```

## Environment Variables

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `API_KEY` | No | `local-dev-secret` | API key expected in `x-api-key` header |
| `OPENAI_API_KEY` | No | unset | Enables optional LLM scam classification |
| `CALLBACK_URL` | No | `https://hackathon.guvi.in/api/updateHoneyPotFinalResult` | GUVI final callback endpoint |
| `REQUEST_TIMEOUT_SECONDS` | No | `3.0` | Callback HTTP timeout |

## Local Run

```bash
cd honeypot-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export API_KEY="my-secret"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test Endpoints

### Health

```bash
curl -s http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

### Honeypot API

```bash
curl -s -X POST "http://localhost:8000/api/honeypot" \
  -H "Content-Type: application/json" \
  -H "x-api-key: my-secret" \
  -d '{
    "sessionId": "wertyu-dfghj-ertyui",
    "message": {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": 1770005528731
    },
    "conversationHistory": [],
    "metadata": {
      "channel": "SMS",
      "language": "English",
      "locale": "IN"
    }
  }'
```

Expected response format:

```json
{"status":"success","reply":"I didn't understand. Which bank is this about?"}
```

## Docker Build & Run

```bash
cd honeypot-api
docker build -t guvi-honeypot-api .
docker run --rm -p 8000:8000 -e API_KEY=my-secret guvi-honeypot-api
```

## Deployment Notes

- Deploy behind HTTPS (e.g., AWS ECS/Fargate, Render, Fly.io, Railway, GCP Cloud Run).
- Set `API_KEY` to a strong random secret.
- Keep callback timeout small to maintain low latency.
- Use process manager autoscaling based on request volume.

## API Contract

### Request

```json
{
  "sessionId": "string",
  "message": { "sender": "scammer", "text": "string", "timestamp": 1770005528731 },
  "conversationHistory": [{ "sender": "scammer", "text": "...", "timestamp": 1770005528731 }],
  "metadata": { "channel": "SMS", "language": "English", "locale": "IN" }
}
```

### Success Response

```json
{ "status": "success", "reply": "string" }
```

### Error Response

```json
{ "status": "error", "message": "..." }
```

