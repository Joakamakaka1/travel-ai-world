# ai_api

Everything that talks to language models: a streaming chat over NVIDIA-hosted models (local
development) or Amazon Bedrock (deployed), tomorrow retrieval over the scraped city data. No database; authenticates with the bearer token
alone (core_api's HS256 JWT locally, the Cognito pool's RS256 ID token when deployed).

## Run

```bash
cp .env.example .env       # AUTH_MODE + SECRET_KEY or COGNITO_* (same as core_api), LLM_PROVIDER + NVIDIA_API_KEY or BEDROCK_*, CORE_API_URL
uv run uvicorn ai_api.main:app --reload --port 8001    # http://localhost:8001/api/v1/ai/docs
```

## Endpoints (`/api/v1/ai`)

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/chat` | Bearer | SSE stream: `data: {"content"}` ×n, `data: {"thread_id"}` when the exchange was recorded, `data: {"error", "error_code"}` on failure, `data: [DONE]` |
| `GET` | `/health/` | — | |
| `GET` | `/health/provider` | — | 503 when the active provider is not configured (no `NVIDIA_API_KEY`, or an empty `BEDROCK_CHAT_MODEL`); answers its `name` |

Request body: `{"message": "...", "history": [{"role": "user"|"assistant", "content": "..."}],
"thread_id": "..."}` (limits in `schemas/chat.py`; the system prompt is server-side and clients
cannot send one). `thread_id` is optional: without it the answer starts a new conversation and the
stream ends with the id to send back next time.

Full contract: [`docs/api/ai-api.openapi.json`](../../../../docs/api/ai-api.openapi.json).

## Layout (ports and adapters)

```text
ai_api/
├── main.py         lifespan: one provider per process (NVIDIA or Bedrock, by LLM_PROVIDER), on app.state
├── config.py       AISettings: LLM_PROVIDER, NVIDIA_*, BEDROCK_*, CHAT_MAX_TOKENS / CHAT_TEMPERATURE / CHAT_TOP_P
├── prompts.py      CHAT_SYSTEM_PROMPT, RAG_CONTEXT_PROMPT
├── domain/         models.py (Message, Document, GenerationParams, Usage, ChatTrace, ChatTurn) · ports.py (LLMProvider, Retriever, TripGateway, ConversationGateway)
├── application/    stream_chat.py, record_conversation.py — the use cases, depend only on ports
├── infrastructure/ nvidia_provider.py · bedrock_provider.py · providers.py (LLM_PROVIDER → adapter) · sse.py · retry.py · core_api_client.py
├── api/            deps.py (wiring) · v1/endpoints/chat.py, health.py
├── schemas/chat.py
└── testing.py      FakeProvider, FakeConversations, settings_for_tests()
```

Swap the model: `NVIDIA_CHAT_MODEL` in `.env` (NVIDIA retires models without notice; a `410` from
the provider means pick another one on build.nvidia.com); `NVIDIA_THINKING=true` lets reasoning
models think first; tune sampling with `CHAT_*`. Swap the provider: `LLM_PROVIDER=nvidia|bedrock`; a
third one is a new class in `infrastructure/` implementing `LLMProvider`, added to
`providers.build_llm_provider`.

## Bedrock (`LLM_PROVIDER=bedrock`)

`infrastructure/bedrock_provider.py` streams through the Converse API (`converse_stream`) with
boto3. There is no API key: the Lambda's IAM role (Terraform, `infra/aws/lambda.tf`) or your SSO
session (`just aws-login`, `AWS_PROFILE`) signs the requests. `BEDROCK_CHAT_MODEL` and
`BEDROCK_TITLE_MODEL` are cross-region inference profiles (`eu.` prefix: Claude Haiku 4.5 for
answers, Amazon Nova Lite for short jobs such as conversation titles), so requests stay inside the
EU; `BEDROCK_REGION` is where the profile lives. Anthropic models need the one-time use-case form in
the Bedrock console before the first call (an `AccessDeniedException` in the logs means it is
missing). Only `CHAT_TEMPERATURE` is sent (Claude 4.5+ refuses `top_p` alongside it); retries follow
the same `RetryPolicy` as NVIDIA and happen only before the first delta.
`BedrockProvider.complete()` returns one non-streamed answer, optionally from another model
(`model=`), for the title generator. The final stream event's token usage is logged
(`Bedrock usage ...`) so costs can be reconciled with Cost Explorer.

## Recorded conversations

Every answered exchange is kept in `core_api` (tables `chat_threads` and `chat_messages`,
[ADR 0013](../../../../docs/architecture/adr/0013-chat-conversations-in-core-api.md)): `ai_api` has
no database, so it posts them over HTTP with the caller's own token. The answer carries what it was
built on (the retrieved documents), the model, the token counts and how long it took, which is what
makes a test conversation reviewable afterwards.

The text is streamed first and recorded after, so nothing delays the answer. If `core_api` cannot
be reached the chat still answers and only logs a warning; if the given thread no longer exists, a
new one is started. `CHAT_RECORD_CONVERSATIONS=false` turns the whole thing off (useful when
running `ai_api` without `core_api`).

Errors: upstream status codes and bodies never reach the browser. A domain error mid-stream is sent
as `{"error": message, "error_code": CODE}`; anything unexpected is logged with its traceback and
sent as `{"error": "Chat stream failed", "error_code": "INTERNAL"}`.

## Tests

```bash
uv run pytest      # FakeProvider + httpx.MockTransport: no network, no key
```

For agents: [`AGENTS.md`](AGENTS.md).
