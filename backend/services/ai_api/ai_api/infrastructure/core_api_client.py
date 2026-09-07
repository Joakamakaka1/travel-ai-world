"""TripGateway adapter: talk to core_api over HTTP as the calling user.

The user's own bearer token is forwarded, so core_api applies exactly the
permissions it would apply to the browser. No service-to-service secret.
"""

from typing import Any

import httpx

from travel_common.exceptions import ProviderUnavailable


class CoreApiClient:
    def __init__(self, base_url: str, api_prefix: str = "/api/v1") -> None:
        self._base = f"{base_url.rstrip('/')}{api_prefix}"

    async def create_trip(
        self, bearer_token: str, trip: dict[str, Any]
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    f"{self._base}/trips/",
                    json=trip,
                    headers={"Authorization": f"Bearer {bearer_token}"},
                )
            except httpx.HTTPError as exc:
                raise ProviderUnavailable("core_api unreachable") from exc
        resp.raise_for_status()
        return resp.json()
