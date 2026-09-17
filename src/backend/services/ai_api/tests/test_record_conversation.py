"""Recording wraps the answer: text first, then the exchange is kept in core_api."""

from collections.abc import AsyncIterator, Iterable

from ai_api.application.record_conversation import RecordConversation
from ai_api.domain.models import ChatTrace, Document, ThreadSaved, Usage
from ai_api.testing import FakeConversations
from travel_common.exceptions import Forbidden, ProviderUnavailable

FIRST = "00000000-0000-0000-0000-000000000001"
SECOND = "00000000-0000-0000-0000-000000000002"


async def _answer(deltas: Iterable[str]) -> AsyncIterator[str]:
    for delta in deltas:
        yield delta


def _clock(*ticks: float):
    values = iter(ticks)
    return lambda: next(values)


def _trace() -> ChatTrace:
    return ChatTrace(
        documents=[
            Document(
                "wv:en:Berlin/Mitte#see:museum-island",
                "Museum Island...",
                {
                    "name": "Museum Island",
                    "source_url": "https://en.wikivoyage.org/wiki/Berlin/Mitte",
                },
            )
        ],
        usage=Usage(
            model="eu.anthropic.claude-haiku-4-5", input_tokens=812, output_tokens=96
        ),
    )


async def _run(record: RecordConversation, **kwargs) -> list:
    stream = record(
        "tok",
        "¿Qué ver en Mitte?",
        _answer(["Isla ", "de los Museos"]),
        _trace(),
        **kwargs,
    )
    return [event async for event in stream]


async def test_text_first_then_the_exchange_is_saved_in_a_new_thread():
    conversations = FakeConversations()
    record = RecordConversation(conversations, clock=_clock(10.0, 12.5))

    events = await _run(record)

    assert events == ["Isla ", "de los Museos", ThreadSaved(FIRST)]
    question, answer = conversations.threads[FIRST]
    assert (question.role, question.content, question.sources) == (
        "user",
        "¿Qué ver en Mitte?",
        (),
    )
    assert answer.content == "Isla de los Museos"
    assert answer.latency_ms == 2500
    assert (answer.model, answer.input_tokens, answer.output_tokens) == (
        "eu.anthropic.claude-haiku-4-5",
        812,
        96,
    )
    [source] = answer.sources
    assert (source.doc_id, source.title, source.url) == (
        "wv:en:Berlin/Mitte#see:museum-island",
        "Museum Island",
        "https://en.wikivoyage.org/wiki/Berlin/Mitte",
    )


async def test_an_existing_thread_is_continued():
    conversations = FakeConversations()
    await conversations.start_thread("tok")
    record = RecordConversation(conversations)

    events = await _run(record, thread_id=FIRST)

    assert events[-1] == ThreadSaved(FIRST)
    assert len(conversations.threads[FIRST]) == 2
    assert SECOND not in conversations.threads


async def test_an_unusable_thread_is_replaced_by_a_new_one():
    class NotMine(FakeConversations):
        async def append_turn(self, bearer_token, thread_id, turn):
            if thread_id == "someone-elses":
                raise Forbidden()
            await super().append_turn(bearer_token, thread_id, turn)

    conversations = NotMine()
    record = RecordConversation(conversations)

    events = await _run(record, thread_id="someone-elses")

    assert events[-1] == ThreadSaved(FIRST)
    assert [t.role for t in conversations.threads[FIRST]] == ["user", "assistant"]


async def test_core_api_down_still_delivers_the_answer():
    record = RecordConversation(
        FakeConversations(fail_with=ProviderUnavailable("core_api unreachable"))
    )

    events = await _run(record)

    assert events == ["Isla ", "de los Museos"]


async def test_an_empty_answer_is_not_recorded():
    conversations = FakeConversations()
    record = RecordConversation(conversations)

    events = [e async for e in record("tok", "hola", _answer([]), ChatTrace())]

    assert events == []
    assert conversations.threads == {}
