from core_api.models.destination import Destination
from core_api.schemas.destination import DestinationCreate, DestinationUpdate
from core_api.services.base import BaseService


class DestinationService(
    BaseService[Destination, DestinationCreate, DestinationUpdate]
):
    pass
