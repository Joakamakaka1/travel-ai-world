from core_api.models.accommodation import Accommodation
from core_api.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from core_api.services.base import BaseService


class AccommodationService(
    BaseService[Accommodation, AccommodationCreate, AccommodationUpdate]
):
    pass
