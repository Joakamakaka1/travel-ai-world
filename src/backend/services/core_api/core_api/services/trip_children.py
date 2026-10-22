"""The collections inside a trip, handled once for all of them.

Children live in the trip's item (ADR 0023): a write changes the caller's trip and
saves it whole, and a lookup searches only that trip. Lists page in memory.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from travel_common.exceptions import EntityNotFound

from core_api.domain.models import (
    Accommodation,
    Activity,
    Entity,
    ItineraryDay,
    Meal,
    Transportation,
    Trip,
)
from core_api.domain.ports import TripRepository
from core_api.pagination import Page
from core_api.services import apply_changes

Parent = Trip | ItineraryDay


@dataclass(frozen=True, slots=True)
class ChildKind:
    """One collection: its dataclass, its list on the parent, its parent field."""

    entity: type[Entity]
    collection: str
    parent_field: str

    @property
    def name(self) -> str:
        return self.entity.__name__

    def items(self, parent: Parent) -> list[Any]:
        return getattr(parent, self.collection)


ITINERARY_DAYS = ChildKind(ItineraryDay, "itinerary_days", "trip_id")
ACCOMMODATIONS = ChildKind(Accommodation, "accommodations", "trip_id")
TRANSPORTATIONS = ChildKind(Transportation, "transportations", "trip_id")
ACTIVITIES = ChildKind(Activity, "activities", "itinerary_day_id")
MEALS = ChildKind(Meal, "meals", "itinerary_day_id")


@dataclass(frozen=True, slots=True)
class Located:
    """The trip to save, and the node inside it (the trip or a day) holding the list."""

    trip: Trip
    parent: Parent


def list_children(parent: Parent, kind: ChildKind, page: Page = Page()) -> list[Any]:
    return kind.items(parent)[page.skip : page.skip + page.limit]


def get_child(parent: Parent, kind: ChildKind, child_id: UUID) -> Any:
    for child in kind.items(parent):
        if child.id == child_id:
            return child
    raise EntityNotFound(kind.name, child_id)


async def create_child(
    trips: TripRepository, where: Located, kind: ChildKind, data: BaseModel
) -> Any:
    child = kind.entity(**data.model_dump(), **{kind.parent_field: where.parent.id})
    child.check_invariants()
    kind.items(where.parent).append(child)
    await trips.save(where.trip)
    return child


async def update_child(
    trips: TripRepository,
    where: Located,
    kind: ChildKind,
    child_id: UUID,
    data: BaseModel,
) -> Any:
    """Patch a child and save the trip; only the child's `updated_at` moves."""
    child = get_child(where.parent, kind, child_id)
    apply_changes(child, data)
    await trips.save(where.trip)
    return child


async def delete_child(
    trips: TripRepository, where: Located, kind: ChildKind, child_id: UUID
) -> None:
    child = get_child(where.parent, kind, child_id)
    kind.items(where.parent).remove(child)
    await trips.save(where.trip)
