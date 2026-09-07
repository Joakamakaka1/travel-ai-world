"""Activity endpoints — thin controllers over ActivityService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core_api.api.deps import get_activity_service, get_current_user
from travel_common.principal import Principal
from core_api.schemas.activity import ActivityCreate, ActivityResponse, ActivityUpdate
from core_api.services.activity_service import ActivityService

router = APIRouter()


@router.get("/", response_model=list[ActivityResponse])
async def read_activities(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
):
    """Retrieve activities (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_in: ActivityCreate,
    itinerary_day_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
):
    """Create a activity under the given parent."""
    return await service.create(activity_in, itinerary_day_id=itinerary_day_id)


@router.get("/{activity_id}", response_model=ActivityResponse)
async def read_activity(
    activity_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
):
    """Get a activity by ID."""
    return await service.get(activity_id)


@router.put("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    activity_in: ActivityUpdate,
    _principal: Principal = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
):
    """Partially update a activity."""
    return await service.update(await service.get(activity_id), activity_in)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: ActivityService = Depends(get_activity_service),
) -> None:
    """Delete a activity."""
    await service.delete(await service.get(activity_id))
