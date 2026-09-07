from core_api.models.accommodation import Accommodation
from core_api.repositories.base import BaseRepository


class AccommodationRepository(BaseRepository[Accommodation]):
    model = Accommodation
