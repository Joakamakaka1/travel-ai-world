"""The use case only composes messages; providers and retrievers are ports."""

from ai_api.application.stream_chat import StreamChat
from ai_api.domain.models import ChatTrace, Document, Message, Usage
from ai_api.prompts import RAG_CONTEXT_PROMPT
from ai_api.testing import FakeProvider, FakeRetriever
from travel_common.exceptions import ProviderUnavailable

GELLERT = Document(
    "wv:en:Budapest/South Buda#do:gellert-baths",
    "Gellért Baths. Art Nouveau thermal baths at the foot of Gellért Hill.",
    {
        "name": "Gellért Baths",
        "category": "do",
        "district": "South Buda",
        "source_url": "https://en.wikivoyage.org/wiki/Budapest/South_Buda",
    },
)


async def _collect(stream) -> list[str]:
    return [delta async for delta in stream]


def _system_turns(provider: FakeProvider) -> list[str]:
    return [m.content for m in provider.calls[0] if m.role == "system"]


async def test_prepends_system_prompt_and_appends_user_turn():
    provider = FakeProvider(["ok"])
    use_case = StreamChat(provider, system_prompt="be helpful")

    deltas = await _collect(use_case("hola", [Message("assistant", "previo")]))

    assert deltas == ["ok"]
    assert provider.calls[0] == [
        Message("system", "be helpful"),
        Message("assistant", "previo"),
        Message("user", "hola"),
    ]


async def test_retrieved_passages_become_a_second_system_turn():
    provider = FakeProvider(["ok"])
    use_case = StreamChat(provider, "sys", retriever=FakeRetriever([GELLERT]))

    await _collect(use_case("¿Qué balneario me recomiendas en Buda?"))

    passage = (
        "Gellért Baths · do · South Buda\n"
        "Gellért Baths. Art Nouveau thermal baths at the foot of Gellért Hill.\n"
        "Source: https://en.wikivoyage.org/wiki/Budapest/South_Buda"
    )
    assert _system_turns(provider) == [
        "sys",
        RAG_CONTEXT_PROMPT.format(context=passage),
    ]


async def test_only_the_question_is_searched_with_the_configured_limit():
    retriever = FakeRetriever([GELLERT])
    use_case = StreamChat(
        FakeProvider(["ok"]), "sys", retriever=retriever, retrieval_limit=3
    )

    await _collect(use_case("baths?", [Message("user", "earlier question")]))

    assert retriever.searches == [("baths?", 3, None)]


async def test_no_passages_means_no_context_turn():
    provider = FakeProvider(["ok"])
    use_case = StreamChat(provider, "sys", retriever=FakeRetriever([]))

    await _collect(use_case("anything"))

    assert _system_turns(provider) == ["sys"]


async def test_a_failing_store_does_not_take_the_chat_down():
    provider = FakeProvider(["still here"])
    retriever = FakeRetriever(fail_with=ProviderUnavailable("Vector store error"))
    use_case = StreamChat(provider, "sys", retriever=retriever)
    trace = ChatTrace()

    deltas = await _collect(use_case("baths?", trace=trace))

    assert deltas == ["still here"]
    assert _system_turns(provider) == ["sys"]
    assert trace.documents == []


async def test_the_trace_collects_documents_and_provider_usage():
    provider = FakeProvider(
        ["ok"], usage=Usage(model="m", input_tokens=5, output_tokens=1)
    )
    use_case = StreamChat(provider, "sys", retriever=FakeRetriever([GELLERT]))
    trace = ChatTrace()

    await _collect(use_case("baths?", trace=trace))

    assert [d.id for d in trace.documents] == [GELLERT.id]
    assert trace.usage == Usage(model="m", input_tokens=5, output_tokens=1)
