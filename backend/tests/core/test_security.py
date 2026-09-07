"""Tokens round-trip the whole Principal, so stateless services can trust them."""

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import Unauthorized
from app.core.principal import Principal, Role
from app.core.security import create_access_token, principal_from_token


def test_token_round_trips_principal():
    principal = Principal(id=42, email="ada@example.com", role=Role.ADMIN)

    assert principal_from_token(create_access_token(principal)) == principal


def test_token_without_role_claim_is_rejected():
    token = jwt.encode(
        {"sub": "1", "exp": 4_102_444_800}, settings.SECRET_KEY, settings.ALGORITHM
    )

    with pytest.raises(Unauthorized):
        principal_from_token(token)


def test_garbage_token_is_rejected():
    with pytest.raises(Unauthorized):
        principal_from_token("not-a-jwt")
