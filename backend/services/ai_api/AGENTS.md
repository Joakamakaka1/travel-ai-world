# AGENTS.md — ai_api

Read [`backend/AGENTS.md`](../../AGENTS.md) first. `ai_api` owns everything that talks to language
models and retrieval. It has **no database** and never imports `core_api`.

## Layout (ports and adapters)

```text
domain/         Message, Document + Protocols: LLMProvider, Retriever, TripGateway
application/    use cases (StreamChat). Depend only on domain ports.
infrastructure/ adapters: nvidia_provider.py, sse.py, retry.py, core_api_client.py
api/            deps.py (wiring), v1/endpoints/{chat,health}.py
prompts.py      system prompts
testing.py      FakeProvider + test_settings() for any test suite
```

- Routes live under `/api/v1/ai/*` so a proxy can route by prefix. Keep it that way.
- Auth is **stateless**: `principal_from_token(token, settings)`; no user lookup.
- Adding a provider: implement `LLMProvider` in `infrastructure/`, select it in `api/deps.py`.
  The use case and the endpoint do not change.
- Adding RAG: implement `Retriever` in `infrastructure/` (own vector store; never `core_api`'s DB),
  inject it in `get_stream_chat`. Persisting results goes through `TripGateway` with the caller's token.
- SSE wire format to the browser is fixed (`data: {"content"}`, `data: {"error"}`, `data: [DONE]`);
  the frontend's `services/chat.ts` depends on it.
- Retries happen only before any delta has been streamed; after that, fail in-band.

## Commands

```bash
uv run uvicorn ai_api.main:app --reload --port 8001
uv run pytest        # no network, no key: FakeProvider + httpx.MockTransport
```

Env: `.env.example` (`NVIDIA_API_KEY`, `SECRET_KEY` = core_api's, `CORE_API_URL`).
