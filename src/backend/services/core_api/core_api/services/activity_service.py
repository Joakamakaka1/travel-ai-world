from core_api.models.activity import Activity
from core_api.schemas.activity import ActivityCreate, ActivityUpdate
from core_api.services.base import BaseService


class ActivityService(BaseService[Activity, ActivityCreate, ActivityUpdate]):
    pass
