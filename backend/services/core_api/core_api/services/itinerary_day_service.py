from core_api.models.itinerary_day import ItineraryDay
from core_api.schemas.itinerary_day import ItineraryDayCreate, ItineraryDayUpdate
from core_api.services.base import BaseService


class ItineraryDayService(
    BaseService[ItineraryDay, ItineraryDayCreate, ItineraryDayUpdate]
):
    entity_name = "Itinerary day"
