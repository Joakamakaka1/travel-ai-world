"""FastAPI dependables: authentication, RBAC and service wiring."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core_api.config import settings
from travel_common.exceptions import Forbidden
from travel_common.http.auth import extract_bearer_token
from travel_common.principal import Principal
from travel_common.security import principal_from_token
from core_api.db.session import get_db
from core_api.repositories.accommodation_repository import AccommodationRepository
from core_api.repositories.activity_repository import ActivityRepository
from core_api.repositories.base import BaseRepository
from core_api.repositories.destination_repository import DestinationRepository
from core_api.repositories.itinerary_day_repository import ItineraryDayRepository
from core_api.repositories.meal_repository import MealRepository
from core_api.repositories.transportation_repository import TransportationRepository
from core_api.repositories.trip_repository import TripRepository
from core_api.repositories.user_repository import UserRepository
from core_api.services.accommodation_service import AccommodationService
from core_api.services.activity_service import ActivityService
from core_api.services.destination_service import DestinationService
from core_api.services.itinerary_day_service import ItineraryDayService
from core_api.services.meal_service import MealService
from core_api.services.transportation_service import TransportationService
from core_api.services.trip_service import TripService
from core_api.services.user_service import UserService

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


async def get_current_user(
    token: str = Depends(extract_bearer_token),
    user_service: UserService = Depends(get_user_service),
) -> Principal:
    """Verify the JWT, then confirm the account still exists and is active.

    The database is the source of truth for role and status: a revoked or
    demoted user is cut off immediately, not when the token expires.
    """
    claims = principal_from_token(token, settings)
    user = await user_service.get_active(claims.id)
    return Principal(id=user.id, email=user.email, role=user.role)


async def get_current_admin_user(
    principal: Principal = Depends(get_current_user),
) -> Principal:
    if not principal.is_admin:
        raise Forbidden("The user doesn't have enough privileges")
    return principal
