from app.models.destination import Destination
from app.repositories.base import BaseRepository


class DestinationRepository(BaseRepository[Destination]):
    model = Destination
