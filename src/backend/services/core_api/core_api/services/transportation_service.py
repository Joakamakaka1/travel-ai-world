from core_api.models.transportation import Transportation
from core_api.schemas.transportation import TransportationCreate, TransportationUpdate
from core_api.services.base import BaseService


class TransportationService(
    BaseService[Transportation, TransportationCreate, TransportationUpdate]
):
    pass
