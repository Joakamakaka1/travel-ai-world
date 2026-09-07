from core_api.models.destination import Destination
from core_api.repositories.base import BaseRepository


class DestinationRepository(BaseRepository[Destination]):
    model = Destination
