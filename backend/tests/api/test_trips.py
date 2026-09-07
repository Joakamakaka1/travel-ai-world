"""Trips are private: listing, reading and mutating stop at the owner boundary."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.principal import Principal, Role
from app.core.security import create_access_token
from app.models.user import User

TRIPS_URL = "/api/v1/trips/"


async def _user(db: AsyncSession, email: str) -> User:
    user = User(email=email, name=email.split("@")[0], is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _headers(user: User) -> dict[str, str]:
    principal = Principal(id=user.id, email=user.email, role=Role.USER)
    return {"Authorization": f"Bearer {create_access_token(principal)}"}


@pytest.fixture
async def alice(db_session: AsyncSession) -> User:
    return await _user(db_session, "alice@example.com")


@pytest.fixture
async def bob(db_session: AsyncSession) -> User:
    return await _user(db_session, "bob@example.com")


async def test_create_and_list_only_own_trips(
    client: AsyncClient, alice: User, bob: User
):
    created = await client.post(
        TRIPS_URL, json={"title": "Lisboa"}, headers=_headers(alice)
    )
    assert created.status_code == 201
    assert created.json()["user_id"] == alice.id

    alice_trips = await client.get(TRIPS_URL, headers=_headers(alice))
    bob_trips = await client.get(TRIPS_URL, headers=_headers(bob))

    assert [t["title"] for t in alice_trips.json()] == ["Lisboa"]
    assert bob_trips.json() == []


async def test_other_users_trip_is_forbidden(
    client: AsyncClient, alice: User, bob: User
):
    created = await client.post(
        TRIPS_URL, json={"title": "Oporto"}, headers=_headers(alice)
    )
    trip_id = created.json()["id"]

    response = await client.get(f"{TRIPS_URL}{trip_id}", headers=_headers(bob))

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "FORBIDDEN"


async def test_missing_trip_is_not_found(client: AsyncClient, alice: User):
    response = await client.get(
        f"{TRIPS_URL}00000000-0000-0000-0000-000000000000", headers=_headers(alice)
    )

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "Trip not found"


async def test_update_and_delete_own_trip(client: AsyncClient, alice: User):
    headers = _headers(alice)
    trip_id = (
        await client.post(TRIPS_URL, json={"title": "Roma"}, headers=headers)
    ).json()["id"]

    updated = await client.put(
        f"{TRIPS_URL}{trip_id}", json={"title": "Roma 2026"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Roma 2026"

    deleted = await client.delete(f"{TRIPS_URL}{trip_id}", headers=headers)
    assert deleted.status_code == 204
    assert (
        await client.get(f"{TRIPS_URL}{trip_id}", headers=headers)
    ).status_code == 404


async def test_unknown_user_in_valid_token_is_unauthorized(client: AsyncClient):
    ghost = User(id=999_999, email="ghost@example.com")

    response = await client.get(TRIPS_URL, headers=_headers(ghost))

    assert response.status_code == 401
