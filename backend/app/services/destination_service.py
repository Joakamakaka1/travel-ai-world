from app.models.destination import Destination
from app.schemas.destination import DestinationCreate, DestinationUpdate
from app.services.base import BaseService


class DestinationService(
    BaseService[Destination, DestinationCreate, DestinationUpdate]
):
    pass
