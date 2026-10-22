"""Closed vocabularies shared by entities, schemas and (via OpenAPI) the frontend.

Stored as plain strings. A trip's phase is derived, not stored (`domain/models.py`).
"""

import enum


class MealType(enum.StrEnum):
    BREAKFAST = "breakfast"
    BRUNCH = "brunch"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class TransportType(enum.StrEnum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    FERRY = "ferry"
    CAR = "car"
    TAXI = "taxi"
    METRO = "metro"
    WALK = "walk"
    OTHER = "other"


class TransportCategory(enum.StrEnum):
    OUTBOUND = "outbound"
    RETURN = "return"
    INTERNAL = "internal"
