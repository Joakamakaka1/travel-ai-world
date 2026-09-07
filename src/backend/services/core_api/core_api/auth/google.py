"""Google ID token verification (only the auth service needs this)."""

import logging

import httpx

from core_api.config import settings

logger = logging.getLogger(__name__)

TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token via Google's tokeninfo endpoint.

    Returns the claims dict (sub, email, name, picture, aud, ...).
    Raises ValueError if the token is invalid or issued for another app.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(TOKENINFO_URL, params={"id_token": id_token})

    if resp.status_code != 200:
        logger.warning("Google token verification failed: %s", resp.text)
        raise ValueError("Invalid Google token")

    data = resp.json()
    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        logger.warning("Google token audience mismatch: %s", data.get("aud"))
        raise ValueError("Token audience mismatch")
    return data
