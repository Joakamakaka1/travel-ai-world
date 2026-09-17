"""Which LLM adapter the process runs, decided by `LLM_PROVIDER`.

The use case and the endpoints only see the `LLMProvider` port; this is the
one place that knows the concrete adapters.
"""

from ai_api.config import AISettings
from ai_api.infrastructure.bedrock_provider import BedrockProvider
from ai_api.infrastructure.nvidia_provider import NvidiaProvider

ChatProvider = NvidiaProvider | BedrockProvider
"""The adapters `main.lifespan` can put on `app.state.llm_provider`."""


def build_llm_provider(settings: AISettings) -> ChatProvider:
    if settings.LLM_PROVIDER == "bedrock":
        return BedrockProvider.from_settings(settings)
    return NvidiaProvider.from_settings(settings)
