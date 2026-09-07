"""Meal endpoints — thin controllers over MealService."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_meal_service, get_current_user
from app.core.principal import Principal
from app.schemas.meal import MealCreate, MealResponse, MealUpdate
from app.services.meal_service import MealService

router = APIRouter()


@router.get("/", response_model=list[MealResponse])
async def read_meals(
    skip: int = 0,
    limit: int = Query(default=100, ge=1, le=500),
    _principal: Principal = Depends(get_current_user),
    service: MealService = Depends(get_meal_service),
):
    """Retrieve meals (paginated)."""
    return await service.list(skip=skip, limit=limit)


@router.post("/", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
async def create_meal(
    meal_in: MealCreate,
    itinerary_day_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: MealService = Depends(get_meal_service),
):
    """Create a meal under the given parent."""
    return await service.create(meal_in, itinerary_day_id=itinerary_day_id)


@router.get("/{meal_id}", response_model=MealResponse)
async def read_meal(
    meal_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: MealService = Depends(get_meal_service),
):
    """Get a meal by ID."""
    return await service.get(meal_id)


@router.put("/{meal_id}", response_model=MealResponse)
async def update_meal(
    meal_id: UUID,
    meal_in: MealUpdate,
    _principal: Principal = Depends(get_current_user),
    service: MealService = Depends(get_meal_service),
):
    """Partially update a meal."""
    return await service.update(await service.get(meal_id), meal_in)


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(
    meal_id: UUID,
    _principal: Principal = Depends(get_current_user),
    service: MealService = Depends(get_meal_service),
) -> None:
    """Delete a meal."""
    await service.delete(await service.get(meal_id))
