"""Bearer-token extraction shared by every service's `deps.py`."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from travel_common.exceptions import Unauthorized

# tokens come from Cognito or core_api's POST /auth/google, never a password form
bearer_scheme = HTTPBearer(auto_error=False)


async def extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized("Missing or invalid authorization header")
    return credentials.credentials
