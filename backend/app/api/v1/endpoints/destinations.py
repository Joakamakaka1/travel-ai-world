"""Destination endpoints — thin controllers over DestinationService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_destination_service, get_current_user
from app.core.principal import Principal
from app.schemas.destination import (
    DestinationCreate,
    DestinationResponse,
    DestinationUpdate,
)
from app.services.destination_service import DestinationService

router = APIRouter()


@router.get("/", response_model=list[DestinationResponse])
async def read_destinations(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: DestinationService = Depends(get_destination_service),
):
    """Retrieve destinations (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post(
    "/", response_model=DestinationResponse, status_code=status.HTTP_201_CREATED
)
async def create_destination(
    destination_in: DestinationCreate,
    trip_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: DestinationService = Depends(get_destination_service),
):
    """Create a destination under the given parent."""
    return await service.create(destination_in, trip_id=trip_id)


@router.get("/{destination_id}", response_model=DestinationResponse)
async def read_destination(
    destination_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: DestinationService = Depends(get_destination_service),
):
    """Get a destination by ID."""
    return await service.get(destination_id)


@router.put("/{destination_id}", response_model=DestinationResponse)
async def update_destination(
    destination_id: UUID,
    destination_in: DestinationUpdate,
    _principal: Principal = Depends(get_current_user),
    service: DestinationService = Depends(get_destination_service),
):
    """Partially update a destination."""
    return await service.update(await service.get(destination_id), destination_in)


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_destination(
    destination_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: DestinationService = Depends(get_destination_service),
) -> None:
    """Delete a destination."""
    await service.delete(await service.get(destination_id))
