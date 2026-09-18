from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from travel_common.http.app_factory import create_app

from ai_api.api.v1.api_router import api_router
from ai_api.config import get_settings
from ai_api.infrastructure.providers import build_llm_provider, build_retriever


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """One provider (NVIDIA or Bedrock, per LLM_PROVIDER) and one client per process.

    The retriever, when RETRIEVAL_ENABLED, is built the same way: once per
    execution environment, with its own clients, never per request.
    """
    settings = get_settings()
    provider = build_llm_provider(settings)
    retriever = build_retriever(settings)
    app.state.llm_provider = provider
    app.state.retriever = retriever
    try:
        yield
    finally:
        await provider.aclose()
        if retriever is not None:
            await retriever.aclose()


settings = get_settings()
app = create_app(
    settings,
    [api_router],
    docs_prefix=f"{settings.API_V1_STR}{api_router.prefix}",
    lifespan=lifespan,
)
