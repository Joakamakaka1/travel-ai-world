from app.models.itinerary_day import ItineraryDay
from app.schemas.itinerary_day import ItineraryDayCreate, ItineraryDayUpdate
from app.services.base import BaseService


class ItineraryDayService(
    BaseService[ItineraryDay, ItineraryDayCreate, ItineraryDayUpdate]
):
    entity_name = "Itinerary day"
