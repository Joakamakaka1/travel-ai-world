"""The entities `core_api` keeps, as plain dataclasses (ADR 0023).

`Trip` is the aggregate, stored as one item. Services call `check_invariants` before
every write; `version` is the optimistic-concurrency counter, never in a response.
"""

import datetime as dt
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Literal

from travel_common.exceptions import TripLocked, UnprocessableEntity
from travel_common.principal import Role

__all__ = [
    "AccessGrant",
    "Accommodation",
    "Activity",
    "Entity",
    "ItineraryDay",
    "Meal",
    "Transportation",
    "Trip",
    "TripPhase",
    "TripSummary",
    "User",
    "ensure_ordered",
    "normalize_email",
    "phase_of",
    "utc_now",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_ordered[D: (date, datetime)](
    start: D | None, end: D | None, what: str
) -> None:
    if start is not None and end is not None and end < start:
        raise UnprocessableEntity(f"{what}: end must not be before start")


TripPhase = Literal["upcoming", "ongoing", "past"]
"""Where a trip stands relative to today. Derived, never stored (ADR 0019)."""


def phase_of(start: date | None, end: date | None, today: date) -> TripPhase:
    """The phase of a trip running from `start` to `end`, seen from `today`.

    Both boundary days count as ongoing, an open end has not finished, and a trip
    without dates is upcoming.
    """
    if end is not None and end < today:
        return "past"
    if start is not None and start <= today and (end is None or today <= end):
        return "ongoing"
    return "upcoming"


@dataclass(slots=True, kw_only=True)
class Entity:
    """Every entity has a UUID and may declare rules over its own fields."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def check_invariants(self) -> None:
        return None


@dataclass(slots=True, kw_only=True)
class TimestampedEntity(Entity):
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True, kw_only=True)
class User(Entity):
    email: str
    is_active: bool = True
    role: Role = Role.USER
    # profile from Google or Cognito; both identify the account by its email
    auth_provider: str = "google"
    google_id: str | None = None
    name: str | None = None
    picture: str | None = None
    # the token `sub` (ADR 0024): the Cognito sub deployed, the account id locally;
    # the AI traces name users by it, never by email
    subject: str | None = None
    version: int = 0


@dataclass(slots=True, kw_only=True)
class Activity(TimestampedEntity):
    itinerary_day_id: uuid.UUID
    time: str | None = None  # "09:00"
    duration_minutes: int | None = None
    title: str
    description: str | None = None
    category: str | None = None
    cost: Decimal | None = None
    booking_required: bool = False
    booking_url: str | None = None
    rating: float | None = None
    # place details copied when the activity was planned
    location_name: str | None = None
    location_address: str | None = None
    location_city: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    # the planner card it came from: its corpus id, and opaque JSON returned untouched
    source_ref: str | None = None
    card: dict[str, Any] | None = None
    part_of_day: str | None = None


@dataclass(slots=True, kw_only=True)
class Meal(TimestampedEntity):
    itinerary_day_id: uuid.UUID
    time: str | None = None  # "13:00"
    type: str | None = None  # MealType
    restaurant_name: str
    cuisine: str | None = None
    estimated_cost: Decimal | None = None
    rating: float | None = None
    location_name: str | None = None
    location_address: str | None = None
    location_city: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    source_ref: str | None = None
    card: dict[str, Any] | None = None
    part_of_day: str | None = None


@dataclass(slots=True, kw_only=True)
class ItineraryDay(TimestampedEntity):
    trip_id: uuid.UUID
    day_number: int
    date: dt.date | None = None
    title: str | None = None
    description: str | None = None
    estimated_cost: Decimal | None = None
    activities: list[Activity] = field(default_factory=list)
    meals: list[Meal] = field(default_factory=list)


@dataclass(slots=True, kw_only=True)
class Accommodation(TimestampedEntity):
    trip_id: uuid.UUID
    check_in: date | None = None
    check_out: date | None = None
    name: str
    type: str | None = None  # hotel, apartment, ...
    city: str | None = None
    country_code: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    price_per_night: Decimal | None = None
    total_cost: Decimal | None = None
    amenities: list[str] | None = None
    check_in_time: str | None = None
    check_out_time: str | None = None
    source_ref: str | None = None
    card: dict[str, Any] | None = None

    def check_invariants(self) -> None:
        ensure_ordered(self.check_in, self.check_out, "Stay")


@dataclass(slots=True, kw_only=True)
class Transportation(TimestampedEntity):
    trip_id: uuid.UUID
    type: str | None = None  # TransportType
    category: str | None = None  # TransportCategory
    from_location: str | None = None
    to_location: str | None = None
    from_city: str | None = None
    to_city: str | None = None
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    provider: str | None = None
    flight_number: str | None = None
    duration_minutes: int | None = None
    cost: Decimal | None = None
    booking_reference: str | None = None

    def check_invariants(self) -> None:
        ensure_ordered(self.departure_time, self.arrival_time, "Journey")


@dataclass(slots=True, kw_only=True)
class Trip(TimestampedEntity):
    """Aggregate root: everything a user plans for one city (ADR 0019)."""

    user_id: uuid.UUID
    title: str
    description: str | None = None
    image_url: str | None = None

    # the one city; `city_slug` is its corpus name ("budapest"), the key that reopens it
    city_slug: str
    city: str
    country: str
    country_code: str  # ISO 3166-1
    lat: float | None = None
    lng: float | None = None
    # where the traveller leaves from, in their own words ("Madrid")
    origin: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = None
    travelers_adults: int = 1
    travelers_children: int = 0
    travelers_infants: int = 0
    travel_style: list[str] | None = None
    pace_preference: str | None = None
    accommodation_type: str | None = None
    # the planner's budget tier: 1 cheap, 2 mid, 3 splurge
    budget_tier: int | None = None
    budget_total: Decimal | None = None
    budget_currency: str | None = None  # ISO 4217
    budget_accommodation: Decimal | None = None
    budget_food: Decimal | None = None
    budget_activities: Decimal | None = None
    budget_transportation: Decimal | None = None
    budget_other: Decimal | None = None
    ai_weather_forecast: str | None = None
    ai_local_tips: list[str] | None = None

    # the planner draft it came from (a UUID): links it to its AI turns (ADR 0024)
    planner_session_id: str | None = None

    # the rest of the aggregate, stored inside the trip
    itinerary_days: list[ItineraryDay] = field(default_factory=list)
    accommodations: list[Accommodation] = field(default_factory=list)
    transportations: list[Transportation] = field(default_factory=list)

    version: int = 0

    @property
    def phase(self) -> TripPhase:
        """Today's phase on the server's UTC date; derived, so nothing is written."""
        return phase_of(self.start_date, self.end_date, utc_now().date())

    def ensure_editable(self) -> None:
        """Refuse changes once the trip has started (ADR 0019); deleting stays allowed.

        Raises:
            TripLocked: the trip is ongoing or past.
        """
        phase = self.phase
        if phase != "upcoming":
            raise TripLocked(phase=phase)

    def check_invariants(self) -> None:
        ensure_ordered(self.start_date, self.end_date, "Trip dates")


@dataclass(slots=True, kw_only=True)
class TripSummary:
    """What the admin list shows of a trip: the fields GSI2 projects (ADR 0024).

    Read from the index, never saved: the trip itself is the `Trip` item.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    city_slug: str
    city: str
    country_code: str
    start_date: date | None = None
    end_date: date | None = None
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime
    planner_session_id: str | None = None

    @property
    def phase(self) -> TripPhase:
        return phase_of(self.start_date, self.end_date, utc_now().date())


def normalize_email(email: str) -> str:
    """How the access list spells an email: trimmed and lower-cased."""
    return email.strip().lower()


@dataclass
class AccessGrant:
    """An email allowed to use the app (ADR 0026).

    Not an `Entity`: its id is the email, which exists before any sign-in.
    `daily_token_limit`: None = the service default, 0 = unlimited, N = N per UTC day.
    """

    email: str
    added_by: str
    daily_token_limit: int | None = None
    note: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)
