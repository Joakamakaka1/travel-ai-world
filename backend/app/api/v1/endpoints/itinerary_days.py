"""ItineraryDay endpoints — thin controllers over ItineraryDayService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_itinerary_day_service, get_current_user
from app.core.principal import Principal
from app.schemas.itinerary_day import (
    ItineraryDayCreate,
    ItineraryDayResponse,
    ItineraryDayUpdate,
)
from app.services.itinerary_day_service import ItineraryDayService

router = APIRouter()


@router.get("/", response_model=list[ItineraryDayResponse])
async def read_itinerary_days(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: ItineraryDayService = Depends(get_itinerary_day_service),
):
    """Retrieve itinerary days (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post(
    "/", response_model=ItineraryDayResponse, status_code=status.HTTP_201_CREATED
)
async def create_itinerary_day(
    itinerary_day_in: ItineraryDayCreate,
    trip_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ItineraryDayService = Depends(get_itinerary_day_service),
):
    """Create a Itinerary day under the given parent."""
    return await service.create(itinerary_day_in, trip_id=trip_id)


@router.get("/{itinerary_day_id}", response_model=ItineraryDayResponse)
async def read_itinerary_day(
    itinerary_day_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ItineraryDayService = Depends(get_itinerary_day_service),
):
    """Get a Itinerary day by ID."""
    return await service.get(itinerary_day_id)


@router.put("/{itinerary_day_id}", response_model=ItineraryDayResponse)
async def update_itinerary_day(
    itinerary_day_id: UUID,
    itinerary_day_in: ItineraryDayUpdate,
    _principal: Principal = Depends(get_current_user),
    service: ItineraryDayService = Depends(get_itinerary_day_service),
):
    """Partially update a Itinerary day."""
    return await service.update(await service.get(itinerary_day_id), itinerary_day_in)


@router.delete("/{itinerary_day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary_day(
    itinerary_day_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ItineraryDayService = Depends(get_itinerary_day_service),
) -> None:
    """Delete a Itinerary day."""
    await service.delete(await service.get(itinerary_day_id))
