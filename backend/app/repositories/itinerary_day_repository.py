from app.models.itinerary_day import ItineraryDay
from app.repositories.base import BaseRepository


class ItineraryDayRepository(BaseRepository[ItineraryDay]):
    model = ItineraryDay
