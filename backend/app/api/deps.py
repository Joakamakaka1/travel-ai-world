"""FastAPI dependables: authentication, RBAC and service wiring."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Forbidden, Unauthorized
from app.core.principal import Principal
from app.core.security import principal_from_token
from app.db.session import get_db
from app.repositories.accommodation_repository import AccommodationRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.base import BaseRepository
from app.repositories.destination_repository import DestinationRepository
from app.repositories.itinerary_day_repository import ItineraryDayRepository
from app.repositories.meal_repository import MealRepository
from app.repositories.transportation_repository import TransportationRepository
from app.repositories.trip_repository import TripRepository
from app.repositories.user_repository import UserRepository
from app.services.accommodation_service import AccommodationService
from app.services.activity_service import ActivityService
from app.services.destination_service import DestinationService
from app.services.itinerary_day_service import ItineraryDayService
from app.services.meal_service import MealService
from app.services.transportation_service import TransportationService
from app.services.trip_service import TripService
from app.services.user_service import UserService

# ── Service wiring ───────────────────────────────────────────────────────────


def provide[S](
    service_cls: Callable[[Any], S], repository_cls: type[BaseRepository[Any]]
) -> Callable[..., S]:
    """Build a `Depends`-able that wires `service_cls(repository_cls(db))`."""

    def _provider(db: AsyncSession = Depends(get_db)) -> S:
        return service_cls(repository_cls(db))

    _provider.__name__ = f"get_{repository_cls.model.__name__.lower()}_service"
    return _provider


get_user_service = provide(UserService, UserRepository)
get_trip_service = provide(TripService, TripRepository)
get_destination_service = provide(DestinationService, DestinationRepository)
get_itinerary_day_service = provide(ItineraryDayService, ItineraryDayRepository)
get_activity_service = provide(ActivityService, ActivityRepository)
get_meal_service = provide(MealService, MealRepository)
get_accommodation_service = provide(AccommodationService, AccommodationRepository)
get_transportation_service = provide(TransportationService, TransportationRepository)

# ── Authentication ───────────────────────────────────────────────────────────

# Tokens are issued by POST /auth/google, never by a password form.
_bearer_scheme = HTTPBearer(auto_error=False)


async def _extract_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized("Missing or invalid authorization header")
    return credentials.credentials


async def get_current_user(
    token: str = Depends(_extract_token),
    user_service: UserService = Depends(get_user_service),
) -> Principal:
    """Verify the JWT, then confirm the account still exists and is active.

    The database is the source of truth for role and status: a revoked or
    demoted user is cut off immediately, not when the token expires.
    """
    claims = principal_from_token(token)
    user = await user_service.get_active(claims.id)
    return Principal(id=user.id, email=user.email, role=user.role)


async def get_current_admin_user(
    principal: Principal = Depends(get_current_user),
) -> Principal:
    if not principal.is_admin:
        raise Forbidden("The user doesn't have enough privileges")
    return principal
