from app.models.transportation import Transportation
from app.schemas.transportation import TransportationCreate, TransportationUpdate
from app.services.base import BaseService


class TransportationService(
    BaseService[Transportation, TransportationCreate, TransportationUpdate]
):
    pass
