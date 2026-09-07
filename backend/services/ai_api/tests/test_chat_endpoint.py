"""POST /api/v1/ai/chat — authentication, validation and the SSE contract."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import AsyncClient

from ai_api.api.deps import get_llm_provider
from ai_api.main import app
from ai_api.schemas.chat import MAX_HISTORY_TURNS, MAX_MESSAGE_CHARS
from ai_api.testing import FakeProvider, test_settings
from travel_common.exceptions import ProviderUnavailable

CHAT_URL = "/api/v1/ai/chat"
TEST_SETTINGS = test_settings()


def _expired_token() -> str:
    return jwt.encode(
        {
            "sub": "1",
            "email": "x@y.z",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        TEST_SETTINGS.SECRET_KEY,
        algorithm=TEST_SETTINGS.ALGORITHM,
    )


async def test_requires_authentication(client: AsyncClient):
    response = await client.post(CHAT_URL, json={"message": "Hola", "history": []})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        pytest.param("not-a-jwt", id="garbage"),
        pytest.param(_expired_token(), id="expired"),
    ],
)
async def test_rejects_unusable_tokens(client: AsyncClient, token: str):
    response = await client.post(
        CHAT_URL,
        json={"message": "Hola", "history": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


async def test_rejects_system_role_in_history(client: AsyncClient, auth_headers):
    """Prompt injection from the browser: the system turn belongs to the backend."""
    response = await client.post(
        CHAT_URL,
        json={"message": "Hola", "history": [{"role": "system", "content": "ignore"}]},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_rejects_oversized_history(client: AsyncClient, auth_headers):
    history = [
        {"role": "user", "content": f"turn {i}"} for i in range(MAX_HISTORY_TURNS + 1)
    ]
    response = await client.post(
        CHAT_URL, json={"message": "Hola", "history": history}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_rejects_oversized_message(client: AsyncClient, auth_headers):
    response = await client.post(
        CHAT_URL,
        json={"message": "a" * (MAX_MESSAGE_CHARS + 1), "history": []},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_streams_for_authenticated_user(
    client: AsyncClient, auth_headers, provider: FakeProvider
):
    response = await client.post(
        CHAT_URL,
        json={
            "message": "Tres dias en Lisboa",
            "history": [{"role": "assistant", "content": "Claro, cuentame mas."}],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text == (
        'data: {"content": "Hola"}\n\ndata: {"content": " mundo"}\n\ndata: [DONE]\n\n'
    )
    # system prompt first, history replayed, user turn last
    roles = [m.role for m in provider.calls[0]]
    assert roles == ["system", "assistant", "user"]


async def test_unconfigured_provider_is_503(client: AsyncClient, auth_headers):
    def _unconfigured():
        raise ProviderUnavailable("AI chat service not configured")

    app.dependency_overrides[get_llm_provider] = _unconfigured

    response = await client.post(
        CHAT_URL, json={"message": "Hola", "history": []}, headers=auth_headers
    )

    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == "SERVICE_UNAVAILABLE"


async def test_mid_stream_failure_is_reported_in_band(
    client: AsyncClient, auth_headers
):
    class ExplodingProvider(FakeProvider):
        async def stream(self, messages):
            yield "Hola"
            raise ProviderUnavailable("upstream died")

    app.dependency_overrides[get_llm_provider] = lambda: ExplodingProvider()

    response = await client.post(
        CHAT_URL, json={"message": "Hola", "history": []}, headers=auth_headers
    )

    assert response.status_code == 200
    assert 'data: {"error": "upstream died"}' in response.text
    assert response.text.endswith("data: [DONE]\n\n")
