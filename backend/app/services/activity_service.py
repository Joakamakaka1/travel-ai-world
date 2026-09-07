from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.services.base import BaseService


class ActivityService(BaseService[Activity, ActivityCreate, ActivityUpdate]):
    pass
