from app.models.transportation import Transportation
from app.repositories.base import BaseRepository


class TransportationRepository(BaseRepository[Transportation]):
    model = Transportation
