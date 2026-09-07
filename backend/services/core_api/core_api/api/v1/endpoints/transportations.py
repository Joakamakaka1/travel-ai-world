"""Transportation endpoints — thin controllers over TransportationService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core_api.api.deps import get_transportation_service, get_current_user
from travel_common.principal import Principal
from core_api.schemas.transportation import (
    TransportationCreate,
    TransportationResponse,
    TransportationUpdate,
)
from core_api.services.transportation_service import TransportationService

router = APIRouter()


@router.get("/", response_model=list[TransportationResponse])
async def read_transportations(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: TransportationService = Depends(get_transportation_service),
):
    """Retrieve transportations (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post(
    "/", response_model=TransportationResponse, status_code=status.HTTP_201_CREATED
)
async def create_transportation(
    transportation_in: TransportationCreate,
    trip_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: TransportationService = Depends(get_transportation_service),
):
    """Create a transportation under the given parent."""
    return await service.create(transportation_in, trip_id=trip_id)


@router.get("/{transportation_id}", response_model=TransportationResponse)
async def read_transportation(
    transportation_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: TransportationService = Depends(get_transportation_service),
):
    """Get a transportation by ID."""
    return await service.get(transportation_id)


@router.put("/{transportation_id}", response_model=TransportationResponse)
async def update_transportation(
    transportation_id: UUID,
    transportation_in: TransportationUpdate,
    _principal: Principal = Depends(get_current_user),
    service: TransportationService = Depends(get_transportation_service),
):
    """Partially update a transportation."""
    return await service.update(await service.get(transportation_id), transportation_in)


@router.delete("/{transportation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transportation(
    transportation_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: TransportationService = Depends(get_transportation_service),
) -> None:
    """Delete a transportation."""
    await service.delete(await service.get(transportation_id))
