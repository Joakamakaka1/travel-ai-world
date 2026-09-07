"""Trip endpoints — every trip is private to the user who owns it."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core_api.api.deps import get_current_user, get_trip_service
from travel_common.principal import Principal
from core_api.schemas.trip import TripCreate, TripResponse, TripUpdate
from core_api.services.trip_service import TripService

router = APIRouter()


@router.get("/", response_model=list[TripResponse])
async def read_trips(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    principal: Principal = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
):
    """The caller's trips (paginated)."""
    return await service.list_for(principal, skip=skip, limit=limit)


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_in: TripCreate,
    principal: Principal = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
):
    """Create a trip owned by the caller."""
    return await service.create(trip_in, user_id=principal.id)


@router.get("/{trip_id}", response_model=TripResponse)
async def read_trip(
    trip_id: UUID,
    principal: Principal = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
):
    """Get one of the caller's trips."""
    return await service.get_owned(trip_id, principal)


@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID,
    trip_in: TripUpdate,
    principal: Principal = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
):
    """Partially update one of the caller's trips."""
    return await service.update(await service.get_owned(trip_id, principal), trip_in)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    principal: Principal = Depends(get_current_user),
    service: TripService = Depends(get_trip_service),
) -> None:
    """Delete one of the caller's trips."""
    await service.delete(await service.get_owned(trip_id, principal))
