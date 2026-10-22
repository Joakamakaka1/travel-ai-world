"""FastAPI dependables: wiring, authentication, the access list and the trip boundary."""

from uuid import UUID

from fastapi import Depends, Query, Request
from travel_common.exceptions import Forbidden
from travel_common.http.auth import extract_bearer_token

from core_api.auth.google import GoogleTokenInfoVerifier, IdentityVerifier
from core_api.auth.principal import AccountPrincipal
from core_api.config import CoreSettings, get_settings
from core_api.domain.models import Trip
from core_api.domain.ports import (
    AccessGrantRepository,
    TripRepository,
    UserRepository,
)
from core_api.infrastructure.dynamo.repositories import (
    DynamoAccessGrantRepository,
    DynamoTripRepository,
    DynamoUserRepository,
)
from core_api.infrastructure.dynamo.table import DynamoTable
from core_api.pagination import MAX_PAGE_SIZE, Page
from core_api.services.access_service import AccessService
from core_api.services.auth_service import Authenticate, SignIn
from core_api.services.trip_children import ITINERARY_DAYS, Located, get_child
from core_api.services.trip_service import TripService
from core_api.services.user_service import UserService


def page_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=MAX_PAGE_SIZE),
) -> Page:
    return Page(skip=skip, limit=limit)


# the lifespan (`main.py`) builds the table once per process; tests override this
def get_table(request: Request) -> DynamoTable:
    return request.app.state.table


def get_user_repository(table: DynamoTable = Depends(get_table)) -> UserRepository:
    return DynamoUserRepository(table)


def get_trip_repository(table: DynamoTable = Depends(get_table)) -> TripRepository:
    return DynamoTripRepository(table)


def get_access_grant_repository(
    table: DynamoTable = Depends(get_table),
) -> AccessGrantRepository:
    return DynamoAccessGrantRepository(table)


def get_access_service(
    grants: AccessGrantRepository = Depends(get_access_grant_repository),
    settings: CoreSettings = Depends(get_settings),
) -> AccessService:
    return AccessService(grants, settings)


def get_user_service(
    users: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(users)


def get_trip_service(
    request: Request,
    trips: TripRepository = Depends(get_trip_repository),
) -> TripService:
    return TripService(trips, getattr(request.app.state, "record_trip_created", None))


def get_authenticate(
    users: UserService = Depends(get_user_service),
    settings: CoreSettings = Depends(get_settings),
) -> Authenticate:
    return Authenticate(users, settings)


async def get_authenticated_user(
    token: str = Depends(extract_bearer_token),
    authenticate: Authenticate = Depends(get_authenticate),
) -> AccountPrincipal:
    """The account behind the bearer token, without the access check.

    Only for the routes an uninvited person must reach to be told so (`GET /users/me`,
    `GET /users/me/access`); everything else depends on `get_current_user`.
    """
    return await authenticate(token)


async def get_current_user(
    principal: AccountPrincipal = Depends(get_authenticated_user),
    access: AccessService = Depends(get_access_service),
) -> AccountPrincipal:
    """The authenticated account, once the access list lets it in (ADR 0026).

    Raises:
        AccessDenied: the account is not on the access list.
    """
    await access.ensure_allowed(principal)
    return principal


async def get_current_admin_user(
    principal: AccountPrincipal = Depends(get_current_user),
) -> AccountPrincipal:
    if not principal.is_admin:
        raise Forbidden("The user doesn't have enough privileges")
    return principal


def get_identity_verifier(
    settings: CoreSettings = Depends(get_settings),
) -> IdentityVerifier:
    return GoogleTokenInfoVerifier(settings.GOOGLE_CLIENT_ID)


def get_sign_in(
    verifier: IdentityVerifier = Depends(get_identity_verifier),
    users: UserService = Depends(get_user_service),
    settings: CoreSettings = Depends(get_settings),
) -> SignIn:
    return SignIn(verifier, users, settings)


async def get_owned_trip(
    trip_id: UUID,
    principal: AccountPrincipal = Depends(get_current_user),
    trips: TripService = Depends(get_trip_service),
) -> Trip:
    """The caller's trip: the one authorization point for everything inside it.

    It is read with the caller as owner, so another user's trip is a 404.
    """
    return await trips.get_owned(trip_id, principal)


async def get_editable_trip(trip: Trip = Depends(get_owned_trip)) -> Trip:
    """The caller's trip for a write, refused with `TripLocked` once it has started.

    Writes depend on this, reads on `get_owned_trip` (ADR 0019).
    """
    trip.ensure_editable()
    return trip


async def get_owned_trip_node(trip: Trip = Depends(get_owned_trip)) -> Located:
    """The trip as the holder of a trip-level collection (reads)."""
    return Located(trip=trip, parent=trip)


async def get_editable_trip_node(trip: Trip = Depends(get_editable_trip)) -> Located:
    """The trip as the holder of a trip-level collection (writes)."""
    return Located(trip=trip, parent=trip)


async def get_owned_itinerary_day(
    itinerary_day_id: UUID, trip: Trip = Depends(get_owned_trip)
) -> Located:
    """A day found inside the caller's trip, with the trip to save it by."""
    return Located(trip=trip, parent=get_child(trip, ITINERARY_DAYS, itinerary_day_id))


async def get_editable_itinerary_day(
    itinerary_day_id: UUID, trip: Trip = Depends(get_editable_trip)
) -> Located:
    """A day of an editable trip: the lock is checked before the day is read."""
    return Located(trip=trip, parent=get_child(trip, ITINERARY_DAYS, itinerary_day_id))
