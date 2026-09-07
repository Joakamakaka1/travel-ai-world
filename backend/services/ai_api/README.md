# ai_api

Everything that talks to language models: today a streaming chat proxy to NVIDIA-hosted models,
tomorrow retrieval over the scraped city data. No database; authenticates with the JWT alone.

## Run

```bash
cp .env.example .env       # SECRET_KEY (same as core_api), NVIDIA_API_KEY, CORE_API_URL
uv run uvicorn ai_api.main:app --reload --port 8001    # http://localhost:8001/docs
```

## Endpoints (`/api/v1/ai`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/chat` | Bearer | SSE stream: `data: {"content"}` ×n, `data: {"error"}` on failure, `data: [DONE]` |
| `GET` | `/health/` | — | |
| `GET` | `/health/provider` | — | 503 when `NVIDIA_API_KEY` is missing |

Request body: `{"message": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}`
(limits in `schemas/chat.py`; the system prompt is server-side and clients cannot send one).

Full contract: [`docs/api/ai-api.openapi.json`](../../../docs/api/ai-api.openapi.json).

## Layout (ports and adapters)

```text
ai_api/
├── main.py, config.py (AISettings), prompts.py
├── domain/         models.py (Message, Document) · ports.py (LLMProvider, Retriever, TripGateway)
├── application/    stream_chat.py — the use case, depends only on ports
├── infrastructure/ nvidia_provider.py · sse.py · retry.py · core_api_client.py
├── api/            deps.py (wiring) · v1/endpoints/chat.py, health.py
├── schemas/chat.py
└── testing.py      FakeProvider, test_settings()
```

Swap the model: `NVIDIA_CHAT_MODEL` in `.env`. Swap the provider: a new class in
`infrastructure/` implementing `LLMProvider`, selected in `api/deps.py`.

## Tests

```bash
uv run pytest      # FakeProvider + httpx.MockTransport: no network, no key
```

For agents: [`AGENTS.md`](AGENTS.md).
