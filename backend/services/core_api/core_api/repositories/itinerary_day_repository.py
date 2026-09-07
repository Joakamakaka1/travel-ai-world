from core_api.models.itinerary_day import ItineraryDay
from core_api.repositories.base import BaseRepository


class ItineraryDayRepository(BaseRepository[ItineraryDay]):
    model = ItineraryDay
