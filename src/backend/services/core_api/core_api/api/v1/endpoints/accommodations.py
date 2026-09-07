"""Accommodation endpoints — thin controllers over AccommodationService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core_api.api.deps import get_accommodation_service, get_current_user
from travel_common.principal import Principal
from core_api.schemas.accommodation import (
    AccommodationCreate,
    AccommodationResponse,
    AccommodationUpdate,
)
from core_api.services.accommodation_service import AccommodationService

router = APIRouter()


@router.get("/", response_model=list[AccommodationResponse])
async def read_accommodations(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: AccommodationService = Depends(get_accommodation_service),
):
    """Retrieve accommodations (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post(
    "/", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED
)
async def create_accommodation(
    accommodation_in: AccommodationCreate,
    trip_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: AccommodationService = Depends(get_accommodation_service),
):
    """Create a accommodation under the given parent."""
    return await service.create(accommodation_in, trip_id=trip_id)


@router.get("/{accommodation_id}", response_model=AccommodationResponse)
async def read_accommodation(
    accommodation_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: AccommodationService = Depends(get_accommodation_service),
):
    """Get a accommodation by ID."""
    return await service.get(accommodation_id)


@router.put("/{accommodation_id}", response_model=AccommodationResponse)
async def update_accommodation(
    accommodation_id: UUID,
    accommodation_in: AccommodationUpdate,
    _principal: Principal = Depends(get_current_user),
    service: AccommodationService = Depends(get_accommodation_service),
):
    """Partially update a accommodation."""
    return await service.update(await service.get(accommodation_id), accommodation_in)


@router.delete("/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accommodation(
    accommodation_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: AccommodationService = Depends(get_accommodation_service),
) -> None:
    """Delete a accommodation."""
    await service.delete(await service.get(accommodation_id))
