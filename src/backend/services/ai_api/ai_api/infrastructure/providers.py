"""Which adapters the process runs: the LLM, decided by `LLM_PROVIDER`, and
the retriever, switched on by `RETRIEVAL_ENABLED`.

The use cases and the endpoints only see the ports; this is the one place that
knows the concrete adapters.
"""

from ai_api.config import AISettings
from ai_api.infrastructure.bedrock_embedder import TitanEmbedder
from ai_api.infrastructure.bedrock_provider import BedrockProvider
from ai_api.infrastructure.nvidia_provider import NvidiaProvider
from ai_api.infrastructure.s3vectors_retriever import S3VectorsRetriever

ChatProvider = NvidiaProvider | BedrockProvider
"""The adapters `main.lifespan` can put on `app.state.llm_provider`."""


def build_llm_provider(settings: AISettings) -> ChatProvider:
    if settings.LLM_PROVIDER == "bedrock":
        return BedrockProvider.from_settings(settings)
    return NvidiaProvider.from_settings(settings)


def build_retriever(settings: AISettings) -> S3VectorsRetriever | None:
    """The vector store the chat searches, or None when retrieval is off.

    Off is the default, and the deployed value until an index holds a corpus:
    the chat then answers from the model's own knowledge and reaches no store.
    """
    if not settings.RETRIEVAL_ENABLED:
        return None
    return S3VectorsRetriever.from_settings(
        settings, TitanEmbedder.from_settings(settings)
    )
