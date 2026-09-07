from core_api.models.transportation import Transportation
from core_api.repositories.base import BaseRepository


class TransportationRepository(BaseRepository[Transportation]):
    model = Transportation
