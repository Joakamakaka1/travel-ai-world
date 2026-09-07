from app.models.accommodation import Accommodation
from app.schemas.accommodation import AccommodationCreate, AccommodationUpdate
from app.services.base import BaseService


class AccommodationService(
    BaseService[Accommodation, AccommodationCreate, AccommodationUpdate]
):
    pass
