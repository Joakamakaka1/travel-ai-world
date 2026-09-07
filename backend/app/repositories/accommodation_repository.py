from app.models.accommodation import Accommodation
from app.repositories.base import BaseRepository


class AccommodationRepository(BaseRepository[Accommodation]):
    model = Accommodation
