# AGENTS.md — ai_api

Read [`backend/AGENTS.md`](../../AGENTS.md) first. `ai_api` owns everything that talks to language
models and retrieval. It has **no database** and never imports `core_api`.

## Layout (ports and adapters)

```text
domain/         Message, ChatRole, Document, GenerationParams, Usage, ChatTrace, ChatTurn, ThreadSaved
                + Protocols: LLMProvider, Retriever, TripGateway, ConversationGateway
application/    use cases (StreamChat, RecordConversation). Depend only on domain ports.
infrastructure/ adapters: nvidia_provider.py, bedrock_provider.py, providers.py (LLM_PROVIDER → adapter), sse.py, retry.py, core_api_client.py
api/            deps.py (per-request wiring; process resources come from app.state), v1/endpoints/{chat,health}.py
main.py         lifespan builds the provider once (providers.build_llm_provider) and closes it on shutdown
prompts.py      every prompt string (system prompt, RAG context template)
testing.py      FakeProvider, FakeConversations + settings_for_tests() for any test suite
```

- Routes live under `/api/v1/ai/*` so a proxy can route by prefix. Keep it that way.
- Auth is **stateless**: `principal_from_token(token, settings)`; no user lookup. `AUTH_MODE` picks
  the issuer (local HS256 with `SECRET_KEY`, or the Cognito pool's RS256 ID tokens against
  `COGNITO_JWKS`); `tests/test_cognito_mode.py` covers the second with `CognitoTestIssuer`.
- Providers: `LLM_PROVIDER` picks NVIDIA (local, API key) or Bedrock (deployed, IAM role, no key;
  `converse_stream` through boto3, run in worker threads). Adding one: implement `LLMProvider` in
  `infrastructure/`, give it `name`, `is_configured` and `aclose()`, and add it to
  `providers.build_llm_provider`. The use case and the endpoint do not change. Sampling comes
  from `AISettings` (`CHAT_*`) as a `GenerationParams`, never from literals in the adapter; Bedrock
  sends only the temperature (Claude 4.5+ rejects it together with `top_p`).
- Adding RAG: implement `Retriever` in `infrastructure/` (own vector store; never `core_api`'s DB),
  inject it in `get_stream_chat`. Persisting results goes through `TripGateway` with the caller's token.
- SSE wire format to the browser is fixed (`data: {"content"}`, `data: {"thread_id"}`,
  `data: {"error", "error_code"}`, `data: [DONE]`); the frontend's `services/chat.ts` depends on it. Upstream bodies and unexpected
  exceptions never reach the client: `sse.py` sends the domain message or a generic one and logs the rest.
- **Conversations live in `core_api`** (ADR 0013), never here: `ai_api` stays stateless and has no
  database. `RecordConversation` wraps the answer stream and, once the answer is complete, appends
  the question and the answer (sources, model, tokens, latency from `ChatTrace`) through
  `ConversationGateway` with the caller's token, then emits `ThreadSaved`. Recording must never
  break a chat: a failure is logged, the answer is already delivered, and an unusable thread is
  replaced by a new one. `CHAT_RECORD_CONVERSATIONS=false` switches it off.
- A provider fills the `Usage` it is handed (model and token counts) by the end of the stream, on
  top of logging it. That is what a recorded answer keeps.
- Retries happen only before any delta has been streamed; after that, fail in-band.

## Commands

```bash
uv run uvicorn ai_api.main:app --reload --port 8001
uv run pytest        # no network, no key: FakeProvider + httpx.MockTransport
```

Env: `.env.example` (`LLM_PROVIDER`, `NVIDIA_API_KEY` or `BEDROCK_*`, `CORE_API_URL`, and the same
`AUTH_MODE`/`SECRET_KEY`/`COGNITO_*` as core_api). Every setting must be documented there
(`tests/test_env_example.py`).
